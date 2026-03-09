"""
Shared PySpark test infrastructure for data transformation tests.

Provides SparkTestMixin that manages a local Spark session for test classes.

Usage:
    from api.test_spark_helpers import SparkTestMixin

    class MySparkTest(SparkTestMixin, TestCase):
        def test_something(self):
            df = self.spark.createDataFrame(...)
"""

from pyspark.sql import SparkSession


class SparkTestMixin:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.spark = (
            SparkSession.builder.appName("test-data-transformation")
            .master("local[2]")
            .config("spark.sql.shuffle.partitions", "2")
            .config("spark.driver.memory", "512m")
            .getOrCreate()
        )

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
        super().tearDownClass()
