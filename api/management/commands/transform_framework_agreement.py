from django.core.management.base import BaseCommand
from pyspark.sql import SparkSession

from api.data_transformation_framework_agreement import transform_framework_agreement


class Command(BaseCommand):
    help = "Run framework agreement ETL and optionally write output"

    def add_arguments(self, parser):
        parser.add_argument("--csv-dir", default="datatransformationlogic", help="Directory for mapping CSVs")
        parser.add_argument("--output", default=None, help="Parquet output path (optional)")
        parser.add_argument(
            "--mapping-table",
            default="api.warehouse_stocks_views.feat_goadmin_map",
            help="Country->region mapping table",
        )

    def handle(self, *args, **options):
        spark = SparkSession.builder.appName("fa-data-transformation").getOrCreate()

        transform_framework_agreement(
            spark,
            csv_dir=options.get("csv_dir"),
            output_path=options.get("output"),
            mapping_table=options.get("mapping_table"),
        )

        spark.stop()
        self.stdout.write(self.style.SUCCESS("Framework agreement transformation completed."))
