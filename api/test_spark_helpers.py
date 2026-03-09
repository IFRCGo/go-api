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
