from django.core.management import CommandError, call_command
from django.core.management.base import BaseCommand

from api.logger import logger


class Command(BaseCommand):
    help = "Run SPARK data transformations for framework agreements and stock inventory"

    def add_arguments(self, parser):
        parser.add_argument(
            "--only-framework-agreements",
            action="store_true",
            default=False,
            help="Only run framework agreements transformation",
        )
        parser.add_argument(
            "--only-stock-inventory",
            action="store_true",
            default=False,
            help="Only run stock inventory transformation",
        )

        # Framework agreement options
        parser.add_argument(
            "--framework-csv-dir",
            default="api/datatransformationlogic",
            help="CSV directory for framework agreement mappings",
        )
        parser.add_argument(
            "--framework-output",
            default=None,
            help="Optional parquet output path for framework agreement transformation",
        )
        parser.add_argument(
            "--framework-mapping-table",
            default="api.stock_inventory_view.feat_goadmin_map",
            help="Country->region mapping table for framework agreement transformation",
        )

        # Stock inventory options
        parser.add_argument(
            "--stock-dry-run",
            action="store_true",
            default=False,
            help="Run stock inventory transformation without writing to database",
        )
        parser.add_argument(
            "--stock-limit",
            type=int,
            default=None,
            help="Limit stock inventory output rows (testing only)",
        )
        parser.add_argument(
            "--stock-warehouse-ids",
            type=str,
            default=None,
            help="Comma-separated warehouse IDs for stock inventory transformation",
        )
        parser.add_argument(
            "--stock-export-csv",
            type=str,
            default=None,
            help="Export stock inventory results to CSV path",
        )

    def handle(self, *args, **options):
        only_fa = options.get("only_framework_agreements", False)
        only_si = options.get("only_stock_inventory", False)

        if only_fa and only_si:
            raise CommandError("Use only one of --only-framework-agreements or --only-stock-inventory")

        run_fa = not only_si
        run_si = not only_fa

        if run_fa:
            logger.info("Running framework agreement transformation...")
            try:
                call_command(
                    "transform_framework_agreement",
                    csv_dir=options.get("framework_csv_dir"),
                    output=options.get("framework_output"),
                    mapping_table=options.get("framework_mapping_table"),
                )
                logger.info("Framework agreement transformation completed.")
            except Exception as ex:
                logger.error("Framework agreement transformation failed: %s", ex)
                raise

        if run_si:
            logger.info("Running stock inventory transformation...")
            try:
                call_command(
                    "transform_stock_inventory",
                    dry_run=options.get("stock_dry_run", False),
                    limit=options.get("stock_limit"),
                    warehouse_ids=options.get("stock_warehouse_ids"),
                    export_csv=options.get("stock_export_csv"),
                )
                logger.info("Stock inventory transformation completed.")
            except Exception as ex:
                logger.error("Stock inventory transformation failed: %s", ex)
                raise

        logger.info("SPARK transformations complete.")
