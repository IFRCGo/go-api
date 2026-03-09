"""
Tests for framework agreement PySpark transformation.

run:
docker compose run --rm serve python manage.py test api.test_data_transformation_framework_agreement --keepdb --verbosity=1
"""

import os
import tempfile
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, TransactionTestCase
from pyspark.sql.types import DecimalType, StringType, StructField, StructType

from api.data_transformation_framework_agreement import (
    _queryset_to_spark_df,
    build_base_agreement,
    get_country_region_mapping,
    load_dimension_tables,
    read_csv_mapping,
    transform_and_clean,
    transform_framework_agreement,
)
from api.factories.spark import (
    DimAgreementLineFactory,
    DimProductCategoryFactory,
    DimProductFactory,
    DimVendorFactory,
    DimVendorPhysicalAddressFactory,
    FctAgreementFactory,
)
from api.models import CleanedFrameworkAgreement
from api.test_spark_helpers import SparkTestMixin

GOADMIN_MAPS = (
    {"AE": "ARE", "CH": "CHE"},
    {"ARE": "United Arab Emirates", "CHE": "Switzerland"},
    {"ARE": "Middle East", "CHE": "Europe"},
)


class QuerysetToSparkDfTest(SparkTestMixin, TestCase):
    def test_non_empty_list_creates_dataframe(self):
        rows = [
            {"id": "A001", "name": "Item A"},
            {"id": "A002", "name": "Item B"},
        ]
        df = _queryset_to_spark_df(self.spark, rows)

        self.assertEqual(df.count(), 2)
        self.assertIn("id", df.columns)
        self.assertIn("name", df.columns)

        collected = sorted(df.collect(), key=lambda r: r["id"])
        self.assertEqual(collected[0]["id"], "A001")
        self.assertEqual(collected[1]["name"], "Item B")

    def test_empty_list_raises_on_schema_inference(self):
        from pyspark.errors.exceptions.base import PySparkValueError

        with self.assertRaises(PySparkValueError):
            _queryset_to_spark_df(self.spark, [])


class GetCountryRegionMappingTest(SparkTestMixin, TestCase):
    @patch("api.data_transformation_framework_agreement._fetch_goadmin_maps", return_value=GOADMIN_MAPS)
    def test_returns_dataframe_with_iso_columns(self, _mock):
        df = get_country_region_mapping(self.spark)

        self.assertEqual(set(df.columns), {"iso2", "iso3", "country_name", "region"})
        self.assertEqual(df.count(), 2)

        rows = {r["iso2"]: r for r in df.collect()}
        self.assertEqual(rows["AE"]["iso3"], "ARE")
        self.assertEqual(rows["AE"]["country_name"], "United Arab Emirates")
        self.assertEqual(rows["AE"]["region"], "Middle East")
        self.assertEqual(rows["CH"]["iso3"], "CHE")

    @patch(
        "api.data_transformation_framework_agreement._fetch_goadmin_maps",
        return_value=({"": "ARE", "AE": "", "CH": "CHE"}, {"CHE": "Switzerland"}, {"CHE": "Europe"}),
    )
    def test_skips_entries_with_empty_iso_codes(self, _mock):
        df = get_country_region_mapping(self.spark)
        self.assertEqual(df.count(), 1)
        row = df.collect()[0]
        self.assertEqual(row["iso2"], "CH")

    @patch(
        "api.data_transformation_framework_agreement._fetch_goadmin_maps",
        return_value=({"ae": "are"}, None, None),
    )
    def test_uppercases_and_strips_iso_codes(self, _mock):
        df = get_country_region_mapping(self.spark)

        row = df.collect()[0]
        self.assertEqual(row["iso2"], "AE")
        self.assertEqual(row["iso3"], "ARE")
        self.assertEqual(row["country_name"], "")
        self.assertEqual(row["region"], "")


class ReadCsvMappingTest(SparkTestMixin, TestCase):
    def test_reads_csv_with_header(self):
        csv_content = "Item Code,SPARK Item Category\nPROD001,Medical\nPROD002,Admin\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            path = f.name

        try:
            df = read_csv_mapping(self.spark, path)
            self.assertIn("Item Code", df.columns)
            self.assertIn("SPARK Item Category", df.columns)
            self.assertEqual(df.count(), 2)
        finally:
            Path(path).unlink()

    def test_reads_csv_without_header(self):
        csv_content = "PROD001,Medical\nPROD002,Admin\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            path = f.name

        try:
            df = read_csv_mapping(self.spark, path, header=False)
            self.assertEqual(df.count(), 2)
            self.assertIn("_c0", df.columns)
        finally:
            Path(path).unlink()


class BuildBaseAgreementTest(SparkTestMixin, TestCase):
    @patch("api.data_transformation_framework_agreement.FctAgreement")
    def test_extracts_iso2_and_joins_country_region(self, mock_fct):
        mock_fct.objects.values.return_value = [
            {
                "agreement_id": "PA-001",
                "classification": "Global Items",
                "default_agreement_line_effective_date": date(2024, 1, 1),
                "default_agreement_line_expiration_date": date(2025, 12, 31),
                "workflow_status": "Active",
                "status": "Effective",
                "vendor": "V001",
                "managing_business_unit_organizational_unit": "AE Dubai Office",
            },
        ]

        mapping_df = self.spark.createDataFrame(
            [("AE", "ARE", "United Arab Emirates", "Middle East")],
            ["iso2", "iso3", "country_name", "region"],
        )

        result = build_base_agreement(self.spark, mapping_df)

        self.assertIn("pa_bu_country_name", result.columns)
        self.assertIn("pa_bu_region_name", result.columns)
        self.assertNotIn("iso2", result.columns)
        self.assertNotIn("managing_business_unit_organizational_unit", result.columns)

        row = result.collect()[0]
        self.assertEqual(row["agreement_id"], "PA-001")
        self.assertEqual(row["pa_bu_country_name"], "United Arab Emirates")
        self.assertEqual(row["pa_bu_region_name"], "Middle East")

    @patch("api.data_transformation_framework_agreement.FctAgreement")
    def test_unmatched_iso2_produces_null_country_region(self, mock_fct):
        mock_fct.objects.values.return_value = [
            {
                "agreement_id": "PA-002",
                "classification": "Local Services",
                "default_agreement_line_effective_date": date(2024, 1, 1),
                "default_agreement_line_expiration_date": date(2025, 12, 31),
                "workflow_status": "Draft",
                "status": "On hold",
                "vendor": "V002",
                "managing_business_unit_organizational_unit": "XX Unknown",
            },
        ]

        mapping_df = self.spark.createDataFrame(
            [("AE", "ARE", "United Arab Emirates", "Middle East")],
            ["iso2", "iso3", "country_name", "region"],
        )

        result = build_base_agreement(self.spark, mapping_df)
        row = result.collect()[0]
        self.assertIsNone(row["pa_bu_country_name"])
        self.assertIsNone(row["pa_bu_region_name"])


class LoadDimensionTablesTest(SparkTestMixin, TestCase):
    @patch("api.data_transformation_framework_agreement.DimVendorPhysicalAddress")
    @patch("api.data_transformation_framework_agreement.DimVendor")
    @patch("api.data_transformation_framework_agreement.DimProductCategory")
    @patch("api.data_transformation_framework_agreement.DimAgreementLine")
    @patch("api.data_transformation_framework_agreement.DimProduct")
    def test_returns_expected_keys_and_columns(
        self,
        mock_product,
        mock_agreement_line,
        mock_prod_cat,
        mock_vendor,
        mock_vendor_addr,
    ):
        mock_product.objects.values.return_value = [
            {"id": "PROD001", "type": "Item", "name": "Tarpaulin"},
        ]
        mock_agreement_line.objects.values.return_value = [
            {
                "agreement_id": "PA-001",
                "product": "PROD001",
                "price_per_unit": Decimal("12.50"),
                "product_category": "CAT01",
            },
        ]
        mock_prod_cat.objects.values.return_value.order_by.return_value = [
            {"category_code": "CAT01", "name": "Shelter"},
        ]
        mock_vendor.objects.values.return_value = [
            {"code": "V001", "name": "Acme Corp"},
        ]
        mock_vendor_addr.objects.values.return_value = [
            {
                "id": "V001",
                "valid_from": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "valid_to": datetime(2025, 12, 31, tzinfo=timezone.utc),
                "country": "CHE",
            },
        ]

        result = load_dimension_tables(self.spark)

        self.assertIn("dim_product", result)
        self.assertIn("dim_agreement_line", result)
        self.assertIn("vendor_joined", result)

        dp = result["dim_product"]
        self.assertEqual(set(dp.columns), {"id", "type", "name"})
        self.assertEqual(dp.count(), 1)

        dal = result["dim_agreement_line"]
        self.assertIn("pa_line_procurement_category", dal.columns)
        dal_row = dal.collect()[0]
        self.assertEqual(dal_row["pa_line_procurement_category"], "Shelter")

        vj = result["vendor_joined"]
        expected_cols = {"vendor_code", "vendor_name", "vendor_valid_from", "vendor_valid_to", "vendor_country"}
        self.assertEqual(set(vj.columns), expected_cols)
        vj_row = vj.collect()[0]
        self.assertEqual(vj_row["vendor_name"], "Acme Corp")
        self.assertEqual(vj_row["vendor_country"], "CHE")


class TransformAndCleanTest(SparkTestMixin, TestCase):

    def _build_inputs(
        self,
        classification="Global Items",
        vendor_code="V001",
        product_id="PROD001",
        product_type="Item",
        product_name="Tarpaulin",
        pa_bu_country_name="United Arab Emirates",
        pa_bu_region_name="Middle East",
        price=Decimal("123.456"),
        procurement_category="Shelter",
        product_csv_code="PROD001",
        product_csv_category="Medical, Health",
        procurement_csv_name="Shelter",
        procurement_csv_category="Shelter & Relief",
    ):
        fct_agreement = self.spark.createDataFrame(
            [
                {
                    "agreement_id": "PA-001",
                    "classification": classification,
                    "default_agreement_line_effective_date": date(2024, 1, 1),
                    "default_agreement_line_expiration_date": date(2025, 12, 31),
                    "workflow_status": "Active",
                    "status": "Effective",
                    "vendor": vendor_code,
                    "pa_bu_country_name": pa_bu_country_name,
                    "pa_bu_region_name": pa_bu_region_name,
                }
            ]
        )

        dim_product = self.spark.createDataFrame(
            [(product_id, product_type, product_name)],
            StructType(
                [
                    StructField("id", StringType()),
                    StructField("type", StringType()),
                    StructField("name", StringType()),
                ]
            ),
        )

        dim_agreement_line = self.spark.createDataFrame(
            [("PA-001", product_id, price, procurement_category)],
            StructType(
                [
                    StructField("agreement_id", StringType()),
                    StructField("product", StringType()),
                    StructField("price_per_unit", DecimalType(35, 6)),
                    StructField("pa_line_procurement_category", StringType()),
                ]
            ),
        )

        vendor_joined = self.spark.createDataFrame(
            [(vendor_code, "Acme Corp", datetime(2024, 1, 1), datetime(2025, 12, 31), "CHE")],
            ["vendor_code", "vendor_name", "vendor_valid_from", "vendor_valid_to", "vendor_country"],
        )

        dim_tables = {
            "dim_product": dim_product,
            "dim_agreement_line": dim_agreement_line,
            "vendor_joined": vendor_joined,
        }

        product_categories_df = self.spark.createDataFrame(
            [(product_csv_code, product_csv_category)],
            ["Item Code", "SPARK Item Category"],
        )

        procurement_categories_df = self.spark.createDataFrame(
            [(procurement_csv_name, procurement_csv_category)],
            ["Category Name", "SPARK Item Category"],
        )

        return fct_agreement, dim_tables, product_categories_df, procurement_categories_df

    def _run(self, **kwargs):
        fct, dim, prod_csv, proc_csv = self._build_inputs(**kwargs)
        return transform_and_clean(fct, dim, prod_csv, proc_csv).collect()[0]

    # -- Geographic coverage ---------------------------------------------------

    def test_global_classification_sets_region_countries_covered_to_global(self):
        row = self._run(classification="Global Items")
        self.assertEqual(row["region_countries_covered"], "Global")

    def test_regional_classification_uses_region_name(self):
        row = self._run(classification="Regional Services", pa_bu_region_name="Middle East")
        self.assertEqual(row["region_countries_covered"], "Middle East")

    def test_local_classification_uses_country_name(self):
        row = self._run(classification="Local Items", pa_bu_country_name="Switzerland")
        self.assertEqual(row["region_countries_covered"], "Switzerland")

    def test_unknown_classification_sets_region_countries_covered_to_null(self):
        row = self._run(classification="Other Something")
        self.assertIsNone(row["region_countries_covered"])

    # -- Item type from product ------------------------------------------------

    def test_product_type_item_produces_goods(self):
        row = self._run(product_id="PROD001", product_type="Item")
        self.assertEqual(row["item_type"], "Goods")

    def test_product_type_service_produces_services(self):
        row = self._run(product_id="PROD001", product_type="Service")
        self.assertEqual(row["item_type"], "Services")

    # -- Item type from classification fallback --------------------------------

    def test_no_product_classification_items_produces_goods(self):
        row = self._run(
            product_id=None,
            product_type=None,
            product_name=None,
            classification="Global Items",
            product_csv_code="__NOMATCH__",
        )
        self.assertEqual(row["item_type"], "Goods")

    def test_no_product_classification_services_produces_services(self):
        row = self._run(
            product_id=None,
            product_type=None,
            product_name=None,
            classification="Regional Services",
            product_csv_code="__NOMATCH__",
        )
        self.assertEqual(row["item_type"], "Services")

    # -- Item category ---------------------------------------------------------

    def test_product_present_uses_product_category_mapping(self):
        row = self._run(
            product_id="PROD001",
            product_csv_code="PROD001",
            product_csv_category="Medical, Health",
        )
        self.assertEqual(row["item_category"], "Medical, Health")

    def test_no_product_uses_procurement_category_mapping(self):
        row = self._run(
            product_id=None,
            product_type=None,
            product_name=None,
            procurement_category="Shelter",
            procurement_csv_name="Shelter",
            procurement_csv_category="Shelter & Relief",
            product_csv_code="__NOMATCH__",
        )
        self.assertEqual(row["item_category"], "Shelter & Relief")

    # -- Short description -----------------------------------------------------

    def test_short_description_uses_product_name_when_available(self):
        row = self._run(product_name="Tarpaulin Roll 4x6m")
        self.assertEqual(row["item_service_short_description"], "Tarpaulin Roll 4x6m")

    def test_short_description_falls_back_to_procurement_category(self):
        row = self._run(
            product_id=None,
            product_type=None,
            product_name=None,
            procurement_category="Shelter",
            product_csv_code="__NOMATCH__",
        )
        self.assertEqual(row["item_service_short_description"], "Shelter")

    # -- Owner and price -------------------------------------------------------

    def test_owner_is_always_ifrc(self):
        row = self._run()
        self.assertEqual(row["owner"], "IFRC")

    def test_price_per_unit_is_rounded_to_two_decimals(self):
        row = self._run(price=Decimal("123.456"))
        self.assertAlmostEqual(float(row["price_per_unit"]), 123.46, places=2)

    # -- Dropped columns -------------------------------------------------------

    def test_intermediate_columns_are_dropped(self):
        row = self._run()
        dropped = {
            "fa_geographical_coverage",
            "pa_bu_region_name",
            "pa_bu_country_name",
            "vendor",
            "product_type",
            "product",
            "product_name",
            "classification",
            "vendor_code",
        }
        for col_name in dropped:
            self.assertNotIn(col_name, row.asDict())


class FrameworkAgreementTransformationIntegrationTest(SparkTestMixin, TransactionTestCase):

    def test_transform_pipeline_creates_cleaned_records(self):
        product = DimProductFactory(id="PROD001", name="Tarpaulin", type="Item")
        category = DimProductCategoryFactory(category_code="CAT01", name="Shelter")
        DimAgreementLineFactory(
            agreement_id="PA-TEST001",
            product=product.id,
            price_per_unit=Decimal("99.99"),
            product_category=category.category_code,
        )
        vendor = DimVendorFactory(code="VEND001", name="Acme Corp")
        DimVendorPhysicalAddressFactory(
            id=vendor.code,
            country="CHE",
            valid_from=date(2024, 1, 1),
            valid_to=date(2025, 12, 31),
        )
        FctAgreementFactory(
            agreement_id="PA-TEST001",
            classification="Global Items",
            status="Effective",
            workflow_status="Active",
            vendor=vendor.code,
            managing_business_unit_organizational_unit="AE Dubai Office",
            default_agreement_line_effective_date=date(2024, 1, 1),
            default_agreement_line_expiration_date=date(2025, 12, 31),
        )

        tmp_dir = tempfile.mkdtemp()
        product_csv = os.path.join(tmp_dir, "product_categories_to_use.csv")
        procurement_csv = os.path.join(tmp_dir, "procurement_categories_to_use.csv")

        with open(product_csv, "w") as f:
            f.write("Item Code,SPARK Item Category\n")
            f.write("PROD001,Medical\n")

        with open(procurement_csv, "w") as f:
            f.write("Category Name,SPARK Item Category\n")
            f.write("Shelter,Shelter & Relief\n")

        try:
            with patch(
                "api.data_transformation_framework_agreement._fetch_goadmin_maps",
                return_value=(
                    {"AE": "ARE"},
                    {"ARE": "United Arab Emirates"},
                    {"ARE": "Middle East"},
                ),
            ):
                result_df = transform_framework_agreement(self.spark, csv_dir=tmp_dir)

            rows = result_df.collect()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["agreement_id"], "PA-TEST001")
            self.assertEqual(rows[0]["region_countries_covered"], "Global")
            self.assertEqual(rows[0]["item_type"], "Goods")
            self.assertEqual(rows[0]["item_category"], "Medical")
            self.assertEqual(rows[0]["owner"], "IFRC")
            self.assertEqual(rows[0]["vendor_name"], "Acme Corp")
            self.assertEqual(rows[0]["item_service_short_description"], "Tarpaulin")

            db_records = CleanedFrameworkAgreement.objects.all()
            self.assertEqual(db_records.count(), 1)

            record = db_records.first()
            self.assertEqual(record.agreement_id, "PA-TEST001")
            self.assertEqual(record.region_countries_covered, "Global")
            self.assertEqual(record.item_type, "Goods")
            self.assertEqual(record.owner, "IFRC")

        finally:
            Path(product_csv).unlink(missing_ok=True)
            Path(procurement_csv).unlink(missing_ok=True)
            Path(tmp_dir).rmdir()
