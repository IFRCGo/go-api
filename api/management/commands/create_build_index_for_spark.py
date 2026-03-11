from django.core.management import call_command
from django.core.management.base import BaseCommand

from api.esconnection import ES_CLIENT
from api.logger import logger


class Command(BaseCommand):
    help = "Create and populate Elasticsearch indices for SPARK (framework agreements and stock inventory)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-create",
            action="store_true",
            default=False,
            help="Skip index creation and only run bulk indexing",
        )
        parser.add_argument(
            "--skip-bulk",
            action="store_true",
            default=False,
            help="Skip bulk indexing and only create indices",
        )
        parser.add_argument(
            "--only-framework-agreements",
            action="store_true",
            default=False,
            help="Only process framework agreements index",
        )
        parser.add_argument(
            "--only-stock-inventory",
            action="store_true",
            default=False,
            help="Only process stock inventory index",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Batch size for bulk indexing (default: 500)",
        )

    def handle(self, *args, **options):
        """Run create and bulk index commands for SPARK indices sequentially.

        Order of operations:
            1. Create framework agreements index (if not skipped)
            2. Create stock inventory index (handled by bulk command)
            3. Bulk index framework agreements (if not skipped)
            4. Bulk index stock inventory (if not skipped)
        """
        if ES_CLIENT is None:
            logger.error("Elasticsearch client not configured (ES_CLIENT is None). Aborting.")
            return

        skip_create = options.get("skip_create", False)
        skip_bulk = options.get("skip_bulk", False)
        only_fa = options.get("only_framework_agreements", False)
        only_si = options.get("only_stock_inventory", False)
        batch_size = options.get("batch_size", 500)

        process_fa = not only_si
        process_si = not only_fa

        # Step 1: Create indices
        if not skip_create:
            if process_fa:
                logger.info("Creating framework agreements index...")
                try:
                    call_command("create_cleaned_framework_agreements_index")
                    logger.info("Framework agreements index created successfully.")
                except Exception as ex:
                    logger.error(f"Failed to create framework agreements index: {ex}")
                    raise

            if process_si:
                logger.info(
                    "Skipping explicit stock inventory create step; "
                    "'bulk_index_stock_inventory' creates a versioned index and swaps alias."
                )

        # Step 2: Bulk index data
        if not skip_bulk:
            if process_fa:
                logger.info("Bulk indexing framework agreements...")
                try:
                    call_command("bulk_index_cleaned_framework_agreements", batch_size=batch_size)
                    logger.info("Framework agreements bulk indexing completed.")
                except Exception as ex:
                    logger.error(f"Failed to bulk index framework agreements: {ex}")
                    raise

            if process_si:
                logger.info("Bulk indexing stock inventory...")
                try:
                    call_command("bulk_index_stock_inventory", batch_size=batch_size)
                    logger.info("Stock inventory bulk indexing completed.")
                except Exception as ex:
                    logger.error(f"Failed to bulk index stock inventory: {ex}")
                    raise

        logger.info("SPARK index creation and population complete.")