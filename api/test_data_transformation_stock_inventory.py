"""
run:
docker compose run --rm serve python manage.py test api.test_data_transformation_stock_inventory --keepdb --verbosity=1
"""

import csv
import tempfile
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, TransactionTestCase
from pyspark.sql.types import (
    BooleanType,
    DecimalType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

from api.data_transformation_stock_inventory import (
    apply_product_category_filters,
    apply_transaction_filters,
    apply_transaction_line_filters,
    apply_warehouse_filter,
    export_to_csv,
    transform_stock_inventory,
)
from api.factories.spark import ItemCodeMappingFactory
from api.test_spark_helpers import SparkTestMixin


class ApplyTransactionFiltersTest(SparkTestMixin, TestCase):
    def test_filters_weighted_average_inventory_closing_and_excluded_rows(self):
        schema = StructType(
            [
                StructField("id", StringType(), True),
                StructField("reference_category", StringType(), True),
                StructField("reference_number", StringType(), True),
                StructField("excluded_from_inventory_value", BooleanType(), True),
            ]
        )
        data = [
            ("TXN001", "Purchase", "PO-001", False),
            ("TXN002", "Weighted average inventory closing", "WAC-001", False),
            ("TXN003", "Transfer", "TRF-001", True),
        ]
        self.spark.createDataFrame(data, schema).createOrReplaceTempView("diminventorytransaction")

        apply_transaction_filters(self.spark)

        rows = self.spark.sql("SELECT id FROM diminventorytransaction ORDER BY id").collect()
        self.assertEqual([r["id"] for r in rows], ["TXN001"])


class ApplyWarehouseFilterTest(SparkTestMixin, TestCase):
    def test_filters_to_requested_warehouses(self):
        schema = StructType(
            [
                StructField("id", StringType(), True),
                StructField("site", StringType(), True),
                StructField("name", StringType(), True),
                StructField("postal_address", StringType(), True),
                StructField("country", StringType(), True),
            ]
        )
        data = [
            ("AE1DUB002", "SITE001", "Dubai", "Addr1", "ARE"),
            ("AR1BUE002", "SITE002", "Buenos Aires", "Addr2", "ARG"),
            ("XX1XXX001", "SITE003", "Other", "Addr3", "XXX"),
        ]
        self.spark.createDataFrame(data, schema).createOrReplaceTempView("dimwarehouse")

        apply_warehouse_filter(self.spark, ["AE1DUB002", "AR1BUE002"])

        rows = self.spark.sql("SELECT id FROM dimwarehouse ORDER BY id").collect()
        self.assertEqual([r["id"] for r in rows], ["AE1DUB002", "AR1BUE002"])


class ApplyTransactionLineFiltersTest(SparkTestMixin, TestCase):
    def test_filters_ifrc_invalid_status_non_ok_and_returned(self):
        schema = StructType(
            [
                StructField("id", StringType(), True),
                StructField("item_status", StringType(), True),
                StructField("item_status_name", StringType(), True),
                StructField("product", StringType(), True),
                StructField("voucher_physical", StringType(), True),
                StructField("project", StringType(), True),
                StructField("batch", StringType(), True),
                StructField("warehouse", StringType(), True),
                StructField("owner", StringType(), True),
                StructField("inventory_transaction", StringType(), True),
                StructField("project_category", StringType(), True),
                StructField("activity", StringType(), True),
                StructField("quantity", DecimalType(20, 6), True),
                StructField("cost_amount_posted", DecimalType(20, 6), True),
                StructField("cost_amount_adjustment", DecimalType(20, 6), True),
                StructField("status", StringType(), True),
                StructField("packing_slip", StringType(), True),
                StructField("packing_slip_returned", BooleanType(), True),
            ]
        )
        data = [
            (
                "TXL001",
                "OK",
                "OK",
                "PROD001",
                None,
                None,
                None,
                "AE1DUB002",
                "NS",
                "TXN001",
                None,
                None,
                Decimal("10.0"),
                Decimal("1.0"),
                Decimal("0.0"),
                "Received",
                None,
                False,
            ),
            (
                "TXL002",
                "OK",
                "OK",
                "PROD001",
                None,
                None,
                None,
                "AE1DUB002",
                "foo#ifrc#bar",
                "TXN001",
                None,
                None,
                Decimal("10.0"),
                Decimal("1.0"),
                Decimal("0.0"),
                "Received",
                None,
                False,
            ),
            (
                "TXL003",
                "OK",
                "OK",
                "PROD001",
                None,
                None,
                None,
                "AE1DUB002",
                "NS",
                "TXN001",
                None,
                None,
                Decimal("10.0"),
                Decimal("1.0"),
                Decimal("0.0"),
                "Invalid",
                None,
                False,
            ),
            (
                "TXL004",
                "BAD",
                "BAD",
                "PROD001",
                None,
                None,
                None,
                "AE1DUB002",
                "NS",
                "TXN001",
                None,
                None,
                Decimal("10.0"),
                Decimal("1.0"),
                Decimal("0.0"),
                "Received",
                None,
                False,
            ),
            (
                "TXL005",
                "OK",
                "OK",
                "PROD001",
                None,
                None,
                None,
                "AE1DUB002",
                "NS",
                "TXN001",
                None,
                None,
                Decimal("10.0"),
                Decimal("1.0"),
                Decimal("0.0"),
                "Received",
                None,
                True,
            ),
        ]
        self.spark.createDataFrame(data, schema).createOrReplaceTempView("diminventorytransactionline")

        apply_transaction_line_filters(self.spark)

        rows = self.spark.sql("SELECT id FROM diminventorytransactionline ORDER BY id").collect()
        self.assertEqual([r["id"] for r in rows], ["TXL001"])


class ApplyProductCategoryFiltersTest(SparkTestMixin, TestCase):
    def test_filters_services_case_insensitive(self):
        schema = StructType(
            [
                StructField("category_code", StringType(), True),
                StructField("name", StringType(), True),
                StructField("parent_category_code", StringType(), True),
                StructField("level", IntegerType(), True),
            ]
        )
        data = [
            ("CAT001", "Goods", None, 1),
            ("CAT002", "services", None, 1),
            ("CAT003", "SERVICES", None, 1),
        ]
        self.spark.createDataFrame(data, schema).createOrReplaceTempView("dimproductcategory")

        apply_product_category_filters(self.spark)

        rows = self.spark.sql("SELECT category_code FROM dimproductcategory ORDER BY category_code").collect()
        self.assertEqual([r["category_code"] for r in rows], ["CAT001"])


class ExportToCsvTest(SparkTestMixin, TestCase):
    def test_exports_api_stockinventory_to_csv(self):
        schema = StructType(
            [
                StructField("warehouse_id", StringType(), True),
                StructField("warehouse", StringType(), True),
                StructField("warehouse_country", StringType(), True),
                StructField("product_category", StringType(), True),
                StructField("item_name", StringType(), True),
                StructField("quantity", DecimalType(18, 2), True),
                StructField("unit_measurement", StringType(), True),
            ]
        )
        data = [
            ("WH001", "Dubai", "ARE", "Goods", "Item A", Decimal("100.00"), "ea"),
            ("WH002", "Buenos Aires", "ARG", "Goods", "Item B", Decimal("50.00"), "kg"),
        ]
        test_df = self.spark.createDataFrame(data, schema)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmp:
            out_path = tmp.name

        try:
            with (
                patch(
                    "api.data_transformation_stock_inventory.load_jdbc_table",
                    return_value=test_df,
                ),
                patch("api.data_transformation_stock_inventory.get_jdbc_config", return_value={}),
            ):
                export_to_csv(self.spark, out_path)
            self.assertTrue(Path(out_path).exists())
            with open(out_path, newline="") as csv_file:
                rows = list(csv.DictReader(csv_file))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["warehouse_id"], "WH001")
        finally:
            if Path(out_path).exists():
                Path(out_path).unlink()


class StockInventoryTransformationIntegrationTest(SparkTestMixin, TransactionTestCase):
    def test_transform_pipeline_with_real_spark_session(self):
        ItemCodeMappingFactory(code="PROD001", url="https://example.com/catalog/prod001")

        warehouse_schema = StructType(
            [
                StructField("id", StringType(), True),
                StructField("site", StringType(), True),
                StructField("name", StringType(), True),
                StructField("postal_address", StringType(), True),
                StructField("country", StringType(), True),
            ]
        )
        warehouse_rows = [
            ("AE1DUB002", "SITE1", "Dubai", "Addr1", "ARE"),
            ("AR1BUE002", "SITE2", "Buenos Aires", "Addr2", "ARG"),
        ]

        product_schema = StructType(
            [
                StructField("id", StringType(), True),
                StructField("name", StringType(), True),
                StructField("type", StringType(), True),
                StructField("unit_of_measure", StringType(), True),
                StructField("product_category", StringType(), True),
                StructField("project_category", StringType(), True),
            ]
        )
        product_rows = [
            ("PROD001", "Item A", "Item", "EA", "CAT001", None),
            ("PROD002", "Service Item", "Item", "EA", "CAT002", None),
        ]

        transaction_line_schema = StructType(
            [
                StructField("id", StringType(), True),
                StructField("item_status", StringType(), True),
                StructField("item_status_name", StringType(), True),
                StructField("product", StringType(), True),
                StructField("voucher_physical", StringType(), True),
                StructField("project", StringType(), True),
                StructField("batch", StringType(), True),
                StructField("warehouse", StringType(), True),
                StructField("owner", StringType(), True),
                StructField("inventory_transaction", StringType(), True),
                StructField("project_category", StringType(), True),
                StructField("activity", StringType(), True),
                StructField("quantity", DecimalType(20, 6), True),
                StructField("cost_amount_posted", DecimalType(20, 6), True),
                StructField("cost_amount_adjustment", DecimalType(20, 6), True),
                StructField("status", StringType(), True),
                StructField("packing_slip", StringType(), True),
                StructField("packing_slip_returned", BooleanType(), True),
            ]
        )
        transaction_line_rows = [
            (
                "TXL001",
                "OK",
                "OK",
                "PROD001",
                None,
                None,
                None,
                "AE1DUB002",
                "NS",
                "TXN001",
                None,
                None,
                Decimal("25.000000"),
                Decimal("5.000000"),
                Decimal("0.000000"),
                "Received",
                None,
                False,
            ),
            (
                "TXL002",
                "OK",
                "OK",
                "PROD002",
                None,
                None,
                None,
                "AE1DUB002",
                "NS",
                "TXN001",
                None,
                None,
                Decimal("10.000000"),
                Decimal("1.000000"),
                Decimal("0.000000"),
                "Received",
                None,
                False,
            ),
        ]

        transaction_schema = StructType(
            [
                StructField("id", StringType(), True),
                StructField("reference_category", StringType(), True),
                StructField("reference_number", StringType(), True),
                StructField("excluded_from_inventory_value", BooleanType(), True),
            ]
        )
        transaction_rows = [("TXN001", "Purchase", "PO-001", False)]

        category_schema = StructType(
            [
                StructField("category_code", StringType(), True),
                StructField("name", StringType(), True),
                StructField("parent_category_code", StringType(), True),
                StructField("level", IntegerType(), True),
            ]
        )
        category_rows = [
            ("CAT001", "Goods", None, 1),
            ("CAT002", "Services", None, 1),
        ]

        isomapping_schema = StructType(
            [
                StructField("iso2", StringType(), True),
                StructField("iso3", StringType(), True),
                StructField("country_name", StringType(), True),
                StructField("region", StringType(), True),
            ]
        )
        isomapping_rows = [("AE", "ARE", "United Arab Emirates", "Middle East")]

        dataframes = {
            "dimwarehouse": self.spark.createDataFrame(warehouse_rows, warehouse_schema),
            "dimproduct": self.spark.createDataFrame(product_rows, product_schema),
            "diminventorytransactionline": self.spark.createDataFrame(transaction_line_rows, transaction_line_schema),
            "diminventorytransaction": self.spark.createDataFrame(transaction_rows, transaction_schema),
            "dimproductcategory": self.spark.createDataFrame(category_rows, category_schema),
        }

        def _fake_country_mapping(spark):
            spark.createDataFrame(isomapping_rows, isomapping_schema).createOrReplaceTempView("isomapping")

        with (
            patch("api.data_transformation_stock_inventory.load_dimension_tables", return_value=dataframes),
            patch("api.data_transformation_stock_inventory.load_country_region_mapping", side_effect=_fake_country_mapping),
        ):
            result_df = transform_stock_inventory(
                self.spark,
                warehouse_codes=["AE1DUB002"],
                dry_run=True,
            )

        rows = result_df.collect()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["warehouse_id"], "AE1DUB002")
        self.assertEqual(rows[0]["item_name"], "Item A")
        self.assertEqual(str(rows[0]["quantity"]), "25.00")
