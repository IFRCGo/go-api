from __future__ import annotations

import os
from datetime import datetime
from decimal import Decimal

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, length, lit
from pyspark.sql.functions import round as spark_round
from pyspark.sql.functions import split as spark_split
from pyspark.sql.functions import substring, trim, when
from pyspark.sql.types import (
    DateType,
    DecimalType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from api.models import (
    CleanedFrameworkAgreement,
    DimAgreementLine,
    DimProduct,
    DimProductCategory,
    DimVendor,
    DimVendorPhysicalAddress,
    FctAgreement,
)
from api.utils import fetch_goadmin_maps as _fetch_goadmin_maps

# --------------------------------------------------------------------------- #
# Django field type → PySpark type mapping                                     #
# --------------------------------------------------------------------------- #
_DJANGO_TO_SPARK = {
    "CharField": StringType(),
    "TextField": StringType(),
    "IntegerField": IntegerType(),
    "BigIntegerField": LongType(),
    "SmallIntegerField": IntegerType(),
    "AutoField": IntegerType(),
    "BigAutoField": LongType(),
    "DateField": DateType(),
    "DateTimeField": TimestampType(),
}


def _django_field_to_spark(field):
    """Map a single Django model field to a PySpark DataType."""
    internal = field.get_internal_type()
    if internal == "DecimalField":
        md = getattr(field, "max_digits", 30) or 30
        dp = getattr(field, "decimal_places", 14) or 14
        return DecimalType(md, dp)
    return _DJANGO_TO_SPARK.get(internal, StringType())


def _schema_for_model(model_cls, column_names: list[str]) -> StructType:
    """Build a PySpark StructType from a Django model for the given columns."""
    field_map = {f.name: f for f in model_cls._meta.concrete_fields}
    fields = []
    for col_name in column_names:
        f = field_map.get(col_name)
        if f is None:
            fields.append(StructField(col_name, StringType(), nullable=True))
        else:
            spark_type = _django_field_to_spark(f)
            nullable = not f.primary_key
            fields.append(StructField(col_name, spark_type, nullable=nullable))
    return StructType(fields)


def _coerce_row(row: dict, schema: StructType) -> dict:
    """Coerce Python values so PySpark accepts them for the given schema.

    - Decimal values stay as Decimal for DecimalType fields
    - Decimal → float for non-DecimalType fields
    - float → Decimal for DecimalType fields
    - datetime → date for DateType fields
    """
    out = {}
    for field in schema.fields:
        val = row.get(field.name)
        if val is None:
            out[field.name] = None
        elif isinstance(field.dataType, DecimalType):
            # DecimalType requires Decimal objects, not float
            if isinstance(val, Decimal):
                out[field.name] = val
            else:
                out[field.name] = Decimal(str(val))
        elif isinstance(val, Decimal):
            out[field.name] = float(val)
        elif isinstance(field.dataType, DateType) and isinstance(val, datetime):
            out[field.name] = val.date()
        else:
            out[field.name] = val
    return out


def _queryset_to_spark_df(spark: SparkSession, rows, schema: StructType | None = None):
    """Create a Spark DataFrame from an iterable of dict-like rows.

    When *schema* is provided it is passed to ``createDataFrame`` so PySpark
    doesn't need to infer types (which fails when every value in a column is
    ``None``).
    """
    rows_list = list(rows)
    if not rows_list:
        return spark.createDataFrame([], schema=schema or StructType([]))
    if schema is not None:
        rows_list = [_coerce_row(r, schema) for r in rows_list]
        return spark.createDataFrame(rows_list, schema=schema)
    return spark.createDataFrame(rows_list)


def get_country_region_mapping(spark: SparkSession, table_name: str = "api.stock_inventory_view.feat_goadmin_map") -> DataFrame:
    """Return a Spark DataFrame with ISO mapping plus `country_name` and `region`.


    Prefer using the existing `_fetch_goadmin_maps()` helper from
    `api.stock_inventory_view` (it fetches live data from GOAdmin). If that
    import or call fails (e.g., running outside Django), fall back to reading
    the provided warehouse table `table_name`.

    Returned columns include both `iso2` and `iso3` so callers can join using
    whichever code they need.
    """
    iso2_to_iso3, iso3_to_country_name, iso3_to_region_name = _fetch_goadmin_maps()

    rows = []
    for iso2, iso3 in (iso2_to_iso3 or {}).items():
        if not iso2 or not iso3:
            continue
        iso2_u = str(iso2).upper().strip()
        iso3_u = str(iso3).upper().strip()
        country_name = iso3_to_country_name.get(iso3_u) if iso3_to_country_name else None
        region_name = iso3_to_region_name.get(iso3_u) if iso3_to_region_name else None
        rows.append(
            {
                "iso2": iso2_u,
                "iso3": iso3_u,
                "country_name": country_name or "",
                "region": region_name or "",
            }
        )

    if rows:
        return spark.createDataFrame(rows)

    df = spark.table(table_name)
    if "iso2" in df.columns:
        df = df.withColumn("iso2", trim(col("iso2")))
    if "iso3" in df.columns:
        df = df.withColumn("iso3", trim(col("iso3")))
    return df


def read_csv_mapping(spark: SparkSession, path: str, header: bool = True) -> DataFrame:
    """Read a CSV mapping into a Spark DataFrame.

    If `header=True` but the first row is entirely blank/empty, the file is
    re-read without a header and the *second* row is used as column names
    (common when CSVs are exported from Excel with a leading empty row).
    """
    df = spark.read.format("csv").option("header", str(header).lower()).load(path)

    if header:
        # Detect an all-empty header row (columns named '', ' ', '_c0', etc.)
        real_names = [c for c in df.columns if c.strip() and not c.startswith("_c")]
        if not real_names:
            # Re-read without header, use second row as header
            df_raw = spark.read.format("csv").option("header", "false").load(path)
            # Row 0 is the empty line, row 1 has real headers
            header_row = df_raw.limit(2).collect()
            if len(header_row) >= 2:
                new_names = [str(v) if v else f"_c{i}" for i, v in enumerate(header_row[1])]
                df_raw = df_raw.toDF(*[f"_c{i}" for i in range(len(df_raw.columns))])
                # Drop the first two rows (empty line + header line)
                from pyspark.sql.functions import monotonically_increasing_id as _mid

                df_raw = df_raw.withColumn("_row_idx", _mid())
                # Get the IDs of the first 2 rows
                first_ids = {r["_row_idx"] for r in df_raw.orderBy("_row_idx").limit(2).collect()}
                df_raw = df_raw.filter(~df_raw["_row_idx"].isin(first_ids)).drop("_row_idx")
                df = df_raw.toDF(*new_names)
    return df


def build_base_agreement(spark: SparkSession, mapping_df: DataFrame) -> DataFrame:
    """Load and prepare the base `fct_agreement` table enriched with mapping."""
    fct_cols = [
        "agreement_id",
        "classification",
        "default_agreement_line_effective_date",
        "default_agreement_line_expiration_date",
        "workflow_status",
        "status",
        "vendor",
        "managing_business_unit_organizational_unit",
    ]
    qs = FctAgreement.objects.values(*fct_cols)
    fct_schema = _schema_for_model(FctAgreement, fct_cols)
    fct_agreement = _queryset_to_spark_df(spark, qs, schema=fct_schema)

    # Extract iso2 from PA org unit and join mapping
    fct_agreement = fct_agreement.withColumn(
        "iso2",
        trim(substring(col("managing_business_unit_organizational_unit"), 1, 2)),
    )

    joined = fct_agreement.join(mapping_df.select("iso2", "country_name", "region"), on="iso2", how="left")

    fct_agreement = (
        joined.withColumnRenamed("country_name", "pa_bu_country_name")
        .withColumnRenamed("region", "pa_bu_region_name")
        .drop("iso2")
        .drop("managing_business_unit_organizational_unit")
    )

    return fct_agreement


def load_dimension_tables(spark: SparkSession) -> dict:
    """Load used dimension tables and return them in a dict."""
    prod_cols = ["id", "type", "name"]
    dim_product = _queryset_to_spark_df(
        spark,
        DimProduct.objects.values(*prod_cols),
        schema=_schema_for_model(DimProduct, prod_cols),
    )

    # dim_agreement_line joined with product category name
    al_cols = ["agreement_id", "product", "price_per_unit", "product_category"]
    dim_agreement_line_df = _queryset_to_spark_df(
        spark,
        DimAgreementLine.objects.values(*al_cols),
        schema=_schema_for_model(DimAgreementLine, al_cols),
    )
    pc_cols = ["category_code", "name"]
    prod_cat_df = _queryset_to_spark_df(
        spark,
        DimProductCategory.objects.values(*pc_cols).order_by(),
        schema=_schema_for_model(DimProductCategory, pc_cols),
    )

    dim_agreement_line = (
        dim_agreement_line_df.alias("dim_al")
        .join(
            prod_cat_df.alias("pc"),
            col("dim_al.product_category") == col("pc.category_code"),
            "left",
        )
        .select(
            col("dim_al.agreement_id").alias("agreement_id"),
            col("dim_al.product").alias("product"),
            col("dim_al.price_per_unit").alias("price_per_unit"),
            col("pc.name").alias("pa_line_procurement_category"),
        )
    )

    # vendor tables
    v_cols = ["code", "name"]
    vendor = _queryset_to_spark_df(
        spark,
        DimVendor.objects.values(*v_cols),
        schema=_schema_for_model(DimVendor, v_cols),
    )
    vpa_cols = ["id", "valid_from", "valid_to", "country"]
    vendor_physical_address = _queryset_to_spark_df(
        spark,
        DimVendorPhysicalAddress.objects.values(*vpa_cols),
        schema=_schema_for_model(DimVendorPhysicalAddress, vpa_cols),
    )

    vendor_joined = (
        vendor.alias("v")
        .join(
            vendor_physical_address.alias("a"),
            col("v.code") == col("a.id"),
            how="left",
        )
        .select(
            col("v.code").alias("vendor_code"),
            col("v.name").alias("vendor_name"),
            col("a.valid_from").alias("vendor_valid_from"),
            col("a.valid_to").alias("vendor_valid_to"),
            col("a.country").alias("vendor_country"),
        )
    )

    return {
        "dim_product": dim_product,
        "dim_agreement_line": dim_agreement_line,
        "vendor_joined": vendor_joined,
    }


def transform_and_clean(
    fct_agreement: DataFrame,
    dim_tables: dict,
    product_categories_df: DataFrame,
    procurement_categories_df: DataFrame,
) -> DataFrame:
    """Apply joins and cleaning rules to produce the final DataFrame.

    This implements the logic translated from the notebook and returns the
    cleaned DataFrame ready for writing or further processing.
    """
    dim_product = dim_tables["dim_product"]
    dim_agreement_line = dim_tables["dim_agreement_line"]
    vendor_joined = dim_tables["vendor_joined"]

    # Join fct_agreement with dim_agreement_line
    agreement_joined = fct_agreement.alias("fct_agreement").join(dim_agreement_line, ["agreement_id"])  # type: ignore[arg-type]

    # Join with product
    agreement_product_joined = (
        agreement_joined.alias("agreement_joined")
        .join(
            dim_product.alias("dim_product"),
            col("agreement_joined.product") == col("dim_product.id"),
            "left",
        )
        .drop("id")
        .withColumnRenamed("name", "product_name")
        .withColumnRenamed("type", "product_type")
    )

    # Final join with vendor
    fa_cleaning = (
        agreement_product_joined.alias("agreement_product_joined")
        .join(
            vendor_joined.alias("vendor_joined"),
            col("agreement_product_joined.vendor") == col("vendor_joined.vendor_code"),
            "left",
        )
        .drop("id")
    )

    # Geographical coverage
    fa_cleaning = fa_cleaning.withColumn(
        "fa_geographical_coverage",
        when(spark_split(col("classification"), " ")[0] == "Global", lit("Global"))
        .when(spark_split(col("classification"), " ")[0] == "Regional", lit("Regional"))
        .when(spark_split(col("classification"), " ")[0] == "Local", lit("Local"))
        .otherwise(lit(None)),
    )

    fa_cleaning = fa_cleaning.withColumn(
        "region_countries_covered",
        when(col("fa_geographical_coverage") == "Global", lit("Global"))
        .when(col("fa_geographical_coverage") == "Regional", col("pa_bu_region_name"))
        .when(col("fa_geographical_coverage") == "Local", col("pa_bu_country_name"))
        .otherwise(lit(None)),
    )

    # Item type rules
    fa_cleaning = fa_cleaning.withColumn(
        "item_type",
        when(
            col("product").isNotNull() & (col("product") != ""),
            when(col("product_type") == "Item", lit("Goods"))
            .when(col("product_type") == "Service", lit("Services"))
            .otherwise(lit(None)),
        ).otherwise(
            when(spark_split(col("classification"), " ")[1] == "Items", lit("Goods"))
            .when(spark_split(col("classification"), " ")[1] == "Services", lit("Services"))
            .otherwise(lit(None))
        ),
    )

    # Join product / procurement category mappings
    final_df = (
        fa_cleaning.alias("s")
        .join(
            product_categories_df.select(
                col("Item Code").alias("pc_item_code"),
                col("SPARK Item Category").alias("product_item_category"),
            ).alias("pc"),
            col("s.product") == col("pc.pc_item_code"),
            "left",
        )
        .join(
            procurement_categories_df.select(
                col("Category Name").alias("proc_category_name"),
                col("SPARK Item Category").alias("procurement_item_category"),
            ).alias("pr"),
            col("s.pa_line_procurement_category") == col("pr.proc_category_name"),
            "left",
        )
        .withColumn(
            "item_category",
            when(col("s.product").isNotNull() & (col("s.product") != ""), col("product_item_category")).otherwise(
                col("procurement_item_category")
            ),
        )
    )

    # Short description
    final_df = final_df.withColumn(
        "item_service_short_description",
        when(col("product_name").isNotNull() & (length(trim(col("product_name"))) > 0), col("product_name")).otherwise(
            col("pa_line_procurement_category")
        ),
    )

    # Owner and price formatting
    final_df = final_df.withColumn("owner", lit("IFRC"))
    final_df = final_df.withColumn("price_per_unit", spark_round(col("price_per_unit"), 2))

    # Drop columns no longer needed (preserve main fields)
    drop_cols = [
        "proc_category_name",
        "product_item_category",
        "procurement_item_category",
        "item_category_product",
        "fa_geographical_coverage",
        "pa_bu_region_name",
        "pa_bu_country_name",
        "vendor",
        "product_type",
        "product",
        "product_name",
        "classification",
        "pc_item_code",
        "vendor_code",
    ]

    # Only drop columns that exist
    existing_drop_cols = [c for c in drop_cols if c in final_df.columns]
    final_df = final_df.drop(*existing_drop_cols)

    return final_df


def transform_framework_agreement(
    spark: SparkSession,
    csv_dir: str = "/home/ifrc/go-api/api/datatransformationlogic",
    output_path=None,
    mapping_table: str = "api.stock_inventory_view.feat_goadmin_map",
) -> DataFrame:
    """Performs the full transformation and writes the result to DB.
    Parameters
    - spark: active SparkSession
    - csv_dir: directory containing `product_categories_to_use.csv` and
      `procurement_categories_to_use.csv` (defaults to `datatransformationlogic`)
    - output_path: if provided, write resulting DataFrame to this path (parquet)
    - mapping_table: table name for country->region mapping
    """
    if not os.path.isdir(csv_dir):
        raise FileNotFoundError(f"CSV mapping directory not found: {csv_dir}")

    mapping_df = get_country_region_mapping(spark, mapping_table)

    fct_agreement = build_base_agreement(spark, mapping_df)

    dim_tables = load_dimension_tables(spark)

    product_categories_path = os.path.join(csv_dir, "product_categories_to_use.csv")
    procurement_categories_path = os.path.join(csv_dir, "procurement_categories_to_use.csv")

    product_categories_df = read_csv_mapping(spark, product_categories_path)
    procurement_categories_df = read_csv_mapping(spark, procurement_categories_path)

    final_df = transform_and_clean(
        fct_agreement,
        dim_tables,
        product_categories_df,
        procurement_categories_df,
    )

    try:
        rows = final_df.collect()
        CleanedFrameworkAgreement.objects.all().delete()

        objs = []
        model_fields = (
            "agreement_id",
            "classification",
            "default_agreement_line_effective_date",
            "default_agreement_line_expiration_date",
            "workflow_status",
            "status",
            "price_per_unit",
            "pa_line_procurement_category",
            "vendor_name",
            "vendor_valid_from",
            "vendor_valid_to",
            "vendor_country",
            "region_countries_covered",
            "item_type",
            "item_category",
            "item_service_short_description",
            "owner",
        )

        for r in rows:
            data = r.asDict(recursive=True)
            kwargs = {f: data.get(f) for f in model_fields if f in data}
            objs.append(CleanedFrameworkAgreement(**kwargs))

        if objs:
            CleanedFrameworkAgreement.objects.bulk_create(objs, batch_size=1000)
    except Exception:
        raise

    return final_df


def main() -> None:
    spark = SparkSession.builder.appName("fa-data-transformation").getOrCreate()
    transform_framework_agreement(spark)
    spark.stop()


if __name__ == "__main__":
    main()
