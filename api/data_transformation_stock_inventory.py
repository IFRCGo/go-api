"""
Stock Inventory Data Transformation using PySpark

This script loads warehouse inventory data from Postgres, applies business logic
filters, joins with mapping tables, and writes the cleaned stock inventory to the
database.

Usage:
    # As a standalone script (requires Django environment)
    python api/data_transformation_stock_inventory.py

    # As a Django management command (recommended)
    docker compose run --rm serve python manage.py transform_stock_inventory
    docker compose run --rm serve python manage.py transform_stock_inventory --dry-run
    docker compose run --rm serve python manage.py transform_stock_inventory --limit 100
    docker compose run --rm serve python manage.py transform_stock_inventory --export-csv stock_inventory.csv
    docker compose run --rm serve python manage.py transform_stock_inventory --warehouse-ids AE1DUB002,AR1BUE002
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional
from urllib.request import urlretrieve

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import StringType, StructField, StructType

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION - Edit these warehouse codes as needed
# ============================================================================

DEFAULT_WAREHOUSE_CODES = [
    "AE1DUB002",  # Dubai
    "AR1BUE002",  # Buenos Aires
    "AU1BRI003",  # Brisbane
    "ES1LAS001",  # Las Palmas
    "GT1GUA001",  # Guatemala
    "HN1COM002",  # Comayagua
    "MY1SEL001",  # Selangor
    "PA1ARR001",  # Arraijan
    "TR1ISTA02",  # Istanbul
]

TRANSACTION_STATUSES = [
    "Deducted",
    "Purchased",
    "Received",
    "Reserved physical",
    "Sold",
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_jdbc_config() -> dict:
    """Get JDBC connection configuration from environment variables."""
    return {
        "host": os.getenv("DJANGO_DB_HOST", "db"),
        "port": os.getenv("DJANGO_DB_PORT", "5432"),
        "database": os.environ["DJANGO_DB_NAME"],
        "user": os.environ["DJANGO_DB_USER"],
        "password": os.environ["DJANGO_DB_PASS"],
        "url": f"jdbc:postgresql://{os.getenv('DJANGO_DB_HOST', 'db')}:{os.getenv('DJANGO_DB_PORT', '5432')}/{os.environ['DJANGO_DB_NAME']}",
    }


def create_spark_session(app_name: str = "stock-inventory-transformation") -> SparkSession:
    """Create and configure a Spark session with PostgreSQL JDBC driver."""
    logger.info("Creating Spark session...")

    # Download PostgreSQL JDBC driver if not present
    postgres_jdbc_version = "42.7.4"
    postgres_jdbc_jar = Path(f"/tmp/postgresql-{postgres_jdbc_version}.jar")
    postgres_jdbc_url = (
        "https://repo1.maven.org/maven2/org/postgresql/postgresql/"
        f"{postgres_jdbc_version}/postgresql-{postgres_jdbc_version}.jar"
    )

    if not postgres_jdbc_jar.exists():
        logger.info(f"Downloading PostgreSQL JDBC driver version {postgres_jdbc_version}...")
        urlretrieve(postgres_jdbc_url, postgres_jdbc_jar)
        logger.info(f"  ✓ JDBC driver downloaded to {postgres_jdbc_jar}")
    else:
        logger.info(f"  ✓ Using existing JDBC driver at {postgres_jdbc_jar}")

    spark_master = os.getenv("SPARK_MASTER", "local[*]")

    spark = (
        SparkSession.builder.appName(app_name)
        .master(spark_master)
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.jars", str(postgres_jdbc_jar))
        .getOrCreate()
    )

    logger.info(f"✓ Spark session created (master: {spark_master})")
    return spark


def load_jdbc_table(spark: SparkSession, jdbc_config: dict, table_name: str) -> DataFrame:
    """Load a single table from Postgres via JDBC."""
    return (
        spark.read.format("jdbc")
        .option("url", jdbc_config["url"])
        .option("dbtable", table_name)
        .option("user", jdbc_config["user"])
        .option("password", jdbc_config["password"])
        .option("driver", "org.postgresql.Driver")
        .load()
    )


# ============================================================================
# MAIN TRANSFORMATION FUNCTIONS
# ============================================================================


def load_dimension_tables(spark: SparkSession) -> dict[str, DataFrame]:
    """Load all required dimension tables from Postgres.

    Returns:
        Dictionary mapping table names to DataFrames
    """
    logger.info("Loading dimension tables from Postgres...")

    jdbc_config = get_jdbc_config()

    tables = {
        "dimwarehouse": "api_dimwarehouse",
        "dimproduct": "api_dimproduct",
        "diminventorytransactionline": "api_diminventorytransactionline",
        "diminventorytransaction": "api_diminventorytransaction",
        "dimproductcategory": "api_dimproductcategory",
    }

    dataframes = {}
    for name, table in tables.items():
        df = load_jdbc_table(spark, jdbc_config, table)
        count = df.count()
        dataframes[name] = df
        logger.info(f"  ✓ {name}: {count:,} rows")

    logger.info("✓ All dimension tables loaded successfully")
    return dataframes


def register_temp_views(dataframes: dict[str, DataFrame]) -> None:
    """Register all DataFrames as temporary SQL views."""
    logger.info("Registering temporary SQL views...")

    for name, df in dataframes.items():
        df.createOrReplaceTempView(name)
        logger.info(f"  ✓ Registered view: {name}")

    logger.info("✓ All views registered")


def apply_transaction_filters(spark: SparkSession) -> None:
    """Apply business logic filters to transaction tables."""
    logger.info("Applying transaction filters...")

    # Filter diminventorytransaction
    logger.info("  - Filtering inventory transactions (excluding weighted average closings)")
    filtered_transactions = spark.sql(
        """
        SELECT *
        FROM diminventorytransaction
        WHERE reference_category NOT ILIKE '%Weighted average inventory closing%'
          AND NOT excluded_from_inventory_value
        ORDER BY id
    """
    )
    filtered_count = filtered_transactions.count()
    filtered_transactions.createOrReplaceTempView("diminventorytransaction")
    logger.info(f"    ✓ {filtered_count:,} transactions after filter")


def apply_warehouse_filter(spark: SparkSession, warehouse_codes: list[str]) -> None:
    """Filter warehouses to specific codes.

    Args:
        spark: Active Spark session
        warehouse_codes: List of warehouse ID codes to include
    """
    logger.info(f"Filtering to {len(warehouse_codes)} specific warehouses...")

    # Build SQL IN clause
    codes_sql = ", ".join(f"'{code}'" for code in warehouse_codes)

    filtered_warehouses = spark.sql(
        f"""
        SELECT *
        FROM dimwarehouse
        WHERE id IN ({codes_sql})
    """
    )

    filtered_count = filtered_warehouses.count()
    filtered_warehouses.createOrReplaceTempView("dimwarehouse")

    logger.info(f"  ✓ Filtered to {filtered_count} warehouses: {', '.join(warehouse_codes)}")


def apply_transaction_line_filters(spark: SparkSession) -> None:
    """Apply filters to inventory transaction lines."""
    logger.info("Applying transaction line filters...")
    logger.info("  - Excluding IFRC-owned items")
    logger.info(f"  - Including only statuses: {', '.join(TRANSACTION_STATUSES)}")
    logger.info("  - Including only 'OK' item status")
    logger.info("  - Excluding returned packing slips")

    statuses_sql = ", ".join(f"'{status}'" for status in TRANSACTION_STATUSES)

    filtered_lines = spark.sql(
        f"""
        SELECT *
        FROM diminventorytransactionline
        WHERE owner NOT ILIKE '%#ifrc%'
          AND status IN ({statuses_sql})
          AND item_status = 'OK'
          AND NOT packing_slip_returned
    """
    )

    filtered_count = filtered_lines.count()
    filtered_lines.createOrReplaceTempView("diminventorytransactionline")
    logger.info(f"  ✓ {filtered_count:,} transaction lines after filters")


def apply_product_category_filters(spark: SparkSession) -> None:
    """Filter out product categories (e.g., services)."""
    logger.info("Applying product category filters...")
    logger.info("  - Excluding 'services' category")

    filtered_categories = spark.sql(
        """
        SELECT *
        FROM dimproductcategory
        WHERE name NOT ILIKE 'services'
    """
    )

    filtered_count = filtered_categories.count()
    filtered_categories.createOrReplaceTempView("dimproductcategory")
    logger.info(f"  ✓ {filtered_count:,} product categories after filter")


def load_country_region_mapping(spark: SparkSession) -> None:
    """Load ISO country to region mappings from the framework agreement module."""
    logger.info("Loading country/region mapping...")

    # Import here to avoid circular dependency and ensure Django is ready
    from api.data_transformation_framework_agreement import get_country_region_mapping

    mapping_df = get_country_region_mapping(spark)
    mapping_count = mapping_df.count()
    mapping_df.createOrReplaceTempView("isomapping")

    logger.info(f"  ✓ Loaded {mapping_count:,} country/region mappings")


def load_item_catalogue_mapping(spark: SparkSession) -> None:
    """Load item code to catalogue URL mappings from Django model."""
    logger.info("Loading item catalogue mappings...")

    # Import here to ensure Django is ready
    from api.models import ItemCodeMapping

    # Allow sync Django ORM calls
    os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

    rows = list(ItemCodeMapping.objects.exclude(code__isnull=True).exclude(url__isnull=True).values("code", "url"))

    schema = StructType(
        [
            StructField("code", StringType(), True),
            StructField("url", StringType(), True),
        ]
    )

    item_mapping_df = spark.createDataFrame(rows, schema=schema)
    item_count = item_mapping_df.count()
    item_mapping_df.createOrReplaceTempView("itemcatalogue")

    logger.info(f"  ✓ Loaded {item_count:,} item catalogue mappings")


def build_stock_inventory_dataframe(spark: SparkSession, limit: Optional[int] = None) -> DataFrame:
    """Build the final stock inventory DataFrame using SQL joins and aggregation.

    Args:
        spark: Active Spark session
        limit: Optional row limit for testing/dry-run

    Returns:
        Final stock inventory DataFrame
    """
    logger.info("Building final stock inventory DataFrame...")

    limit_clause = f"LIMIT {limit}" if limit else ""

    result_df = spark.sql(
        f"""
        SELECT
            w.id AS warehouse_id,
            w.name AS warehouse,
            COALESCE(im.country_name, w.country) AS warehouse_country,
            im.region AS region,
            pc.name AS product_category,
            p.name AS item_name,
            CAST(ROUND(SUM(quantity), 2) AS DECIMAL(18,2)) AS quantity,
            LOWER(p.unit_of_measure) AS unit_measurement,
            ic.url AS catalogue_link
        FROM dimwarehouse w
        JOIN diminventorytransactionline itl
            ON w.id = itl.warehouse
        JOIN diminventorytransaction it
            ON itl.inventory_transaction = it.id
        JOIN dimproduct p
            ON itl.product = p.id
        JOIN dimproductcategory pc
            ON p.product_category = pc.category_code
        LEFT JOIN isomapping im
            ON w.country = im.iso3
        LEFT JOIN itemcatalogue ic
            ON p.id = ic.code
        GROUP BY
            w.name,
            w.id,
            COALESCE(im.country_name, w.country),
            im.region,
            pc.name,
            p.name,
            LOWER(p.unit_of_measure),
            ic.url
        HAVING quantity > 0
        ORDER BY warehouse, product_category, quantity DESC
        {limit_clause}
    """
    )

    result_count = result_df.count()
    logger.info(f"  ✓ Generated {result_count:,} stock inventory records")

    return result_df


def write_to_database(df: DataFrame, dry_run: bool = False) -> None:
    """Write the stock inventory DataFrame to the database.

    Args:
        df: Stock inventory DataFrame to write
        dry_run: If True, only show sample data without writing
    """
    if dry_run:
        logger.info("DRY RUN MODE - Showing sample data (not writing to database):")
        df.show(20, truncate=False)
        logger.info("✓ Dry run complete (no data written)")
        return

    logger.info("Writing stock inventory to database (api_stockinventory table)...")

    jdbc_config = get_jdbc_config()

    df.write.format("jdbc").option("url", jdbc_config["url"]).option("dbtable", "api_stockinventory").option(
        "user", jdbc_config["user"]
    ).option("password", jdbc_config["password"]).option("driver", "org.postgresql.Driver").mode("overwrite").save()

    logger.info("✓ Stock inventory successfully written to database")


def verify_and_display_results(spark: SparkSession, num_rows: int = 20) -> None:
    """Retrieve and display the stock inventory table for verification.

    Args:
        spark: Active Spark session
        num_rows: Number of rows to display (default: 20)
    """
    logger.info(f"Retrieving and displaying {num_rows} rows from api_stockinventory table for verification...")

    jdbc_config = get_jdbc_config()

    try:
        verification_df = load_jdbc_table(spark, jdbc_config, "api_stockinventory")
        total_count = verification_df.count()

        logger.info(f"✓ Total rows in api_stockinventory: {total_count:,}")
        logger.info(f"\nDisplaying first {num_rows} rows:")
        logger.info("=" * 120)

        verification_df.show(num_rows, truncate=False)

        logger.info("=" * 120)
        logger.info("✓ Verification complete")

    except Exception as e:
        logger.error(f"✗ Failed to retrieve verification data: {str(e)}")
        raise


def export_to_csv(spark: SparkSession, output_path: str = "stock_inventory.csv") -> None:
    """Export the stock inventory table to CSV file.

    Args:
        spark: Active Spark session
        output_path: Path where CSV file should be saved (default: stock_inventory.csv)
    """
    logger.info(f"Exporting stock inventory to CSV: {output_path}")

    jdbc_config = get_jdbc_config()

    try:
        # Load the table from database
        df = load_jdbc_table(spark, jdbc_config, "api_stockinventory")
        total_count = df.count()

        logger.info(f"  - Loading {total_count:,} rows from database...")

        # Convert to Pandas and export to CSV
        pandas_df = df.toPandas()
        pandas_df.to_csv(output_path, index=False)

        logger.info(f"✓ Successfully exported {total_count:,} rows to {output_path}")

    except Exception as e:
        logger.error(f"✗ Failed to export CSV: {str(e)}")
        raise


# ============================================================================
# MAIN ORCHESTRATION
# ============================================================================


def transform_stock_inventory(
    spark: SparkSession,
    warehouse_codes: Optional[list[str]] = None,
    dry_run: bool = False,
    limit: Optional[int] = None,
    export_csv: Optional[str] = None,
) -> DataFrame:
    """Main orchestration function for stock inventory transformation.

    Args:
        spark: Active Spark session
        warehouse_codes: Optional list of warehouse codes to filter (defaults to configured list)
        dry_run: If True, show results without writing to database
        limit: Optional row limit for testing
        export_csv: Optional CSV file path to export results after transformation

    Returns:
        Final stock inventory DataFrame
    """
    logger.info("=" * 80)
    logger.info("STOCK INVENTORY TRANSFORMATION STARTED")
    logger.info("=" * 80)

    if warehouse_codes is None:
        warehouse_codes = DEFAULT_WAREHOUSE_CODES

    try:
        # Step 1: Load dimension tables
        dataframes = load_dimension_tables(spark)

        # Step 2: Register SQL views
        register_temp_views(dataframes)

        # Step 3: Apply filters
        apply_transaction_filters(spark)
        apply_warehouse_filter(spark, warehouse_codes)
        apply_transaction_line_filters(spark)
        apply_product_category_filters(spark)

        # Step 4: Load mapping tables
        load_country_region_mapping(spark)
        load_item_catalogue_mapping(spark)

        # Step 5: Build final DataFrame
        result_df = build_stock_inventory_dataframe(spark, limit=limit)

        # Step 6: Write to database
        write_to_database(result_df, dry_run=dry_run)

        # Step 7: Verify results (unless dry run)
        if not dry_run:
            verify_and_display_results(spark, num_rows=20)

        # Step 8: Export to CSV if requested (unless dry run)
        if export_csv and not dry_run:
            export_to_csv(spark, output_path=export_csv)

        logger.info("=" * 80)
        logger.info("✓ STOCK INVENTORY TRANSFORMATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)

        return result_df

    except Exception as e:
        logger.error("=" * 80)
        logger.error("✗ STOCK INVENTORY TRANSFORMATION FAILED")
        logger.error("=" * 80)
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error("Check the logs above to identify which step failed.")
        raise


def main() -> None:
    """Main entry point for standalone script execution."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Ensure Django is set up
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")
    import django

    django.setup()

    # Create Spark session
    spark = create_spark_session()

    try:
        transform_stock_inventory(spark)
    finally:
        logger.info("Stopping Spark session...")
        spark.stop()
        logger.info("✓ Spark session stopped")


if __name__ == "__main__":
    main()
