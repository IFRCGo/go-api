"""
Tests for framework agreement PySpark transformation.

run:
docker compose run --rm serve python manage.py test api.test_data_transformation_framework_agreement --keepdb --verbosity=1
"""

import tempfile
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase
from pyspark.sql.types import (
    DateType,
    DecimalType,
    StringType,
    StructField,
    StructType,
)

from api.data_transformation_framework_agreement import (
    _queryset_to_spark_df,
    build_base_agreement,
    get_country_region_mapping,
    load_dimension_tables,
    read_csv_mapping,
)
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

    def test_empty_list_creates_empty_dataframe(self):
        df = _queryset_to_spark_df(self.spark, [])
        self.assertEqual(df.count(), 0)


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
        return_value=({"": "ARE", "AE": ""}, {}, {}),
    )
    def test_skips_entries_with_empty_iso_codes(self, _mock):
        df = get_country_region_mapping(self.spark)
        self.assertEqual(df.count(), 0)

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
                "default_agreement_line_effective_date": None,
                "default_agreement_line_expiration_date": None,
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

        # dim_product
        dp = result["dim_product"]
        self.assertEqual(set(dp.columns), {"id", "type", "name"})
        self.assertEqual(dp.count(), 1)

        # dim_agreement_line has pa_line_procurement_category from the category join
        dal = result["dim_agreement_line"]
        self.assertIn("pa_line_procurement_category", dal.columns)
        dal_row = dal.collect()[0]
        self.assertEqual(dal_row["pa_line_procurement_category"], "Shelter")

        # vendor_joined
        vj = result["vendor_joined"]
        expected_cols = {"vendor_code", "vendor_name", "vendor_valid_from", "vendor_valid_to", "vendor_country"}
        self.assertEqual(set(vj.columns), expected_cols)
        vj_row = vj.collect()[0]
        self.assertEqual(vj_row["vendor_name"], "Acme Corp")
        self.assertEqual(vj_row["vendor_country"], "CHE")
