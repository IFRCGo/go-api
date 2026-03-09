"""
Django management command for stock inventory transformation.

Usage:
    # Run full transformation
    python manage.py transform_stock_inventory

    # Dry run (show results without writing to database)
    python manage.py transform_stock_inventory --dry-run

    # Limit output rows (for testing)
    python manage.py transform_stock_inventory --limit 100

    # Use custom warehouse codes
    python manage.py transform_stock_inventory --warehouse-ids AE1DUB002,AR1BUE002,ES1LAS001

    # Combine options
    python manage.py transform_stock_inventory --dry-run --limit 50 --warehouse-ids AE1DUB002
"""

import logging

from django.core.management.base import BaseCommand

from api.data_transformation_stock_inventory import DEFAULT_WAREHOUSE_CODES, create_spark_session, transform_stock_inventory


class Command(BaseCommand):
    help = "Transform and load stock inventory data using PySpark"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show results without writing to database",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of output rows (useful for testing)",
        )
        parser.add_argument(
            "--warehouse-ids",
            type=str,
            default=None,
            help="Comma-separated warehouse IDs to filter (e.g., 'AE1DUB002,AR1BUE002')",
        )

    def handle(self, *args, **options):
        # Configure logging for better CLI output
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Parse options
        dry_run = options.get("dry_run", False)
        limit = options.get("limit")
        warehouse_ids_str = options.get("warehouse_ids")

        # Parse warehouse IDs if provided
        if warehouse_ids_str:
            warehouse_codes = [code.strip() for code in warehouse_ids_str.split(",")]
            self.stdout.write(self.style.WARNING(f"Using custom warehouse codes: {', '.join(warehouse_codes)}"))
        else:
            warehouse_codes = DEFAULT_WAREHOUSE_CODES
            self.stdout.write(f"Using default warehouse codes ({len(warehouse_codes)} warehouses)")

        # Show run mode
        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN MODE - No data will be written to database"))
        if limit:
            self.stdout.write(self.style.WARNING(f"⚠️  LIMIT MODE - Processing only {limit} rows"))

        # Create Spark session (with JDBC driver download)
        spark = create_spark_session()

        try:
            # Run transformation
            transform_stock_inventory(
                spark,
                warehouse_codes=warehouse_codes,
                dry_run=dry_run,
                limit=limit,
            )

            # Success message
            if dry_run:
                self.stdout.write(self.style.SUCCESS("✓ Dry run completed successfully"))
            else:
                self.stdout.write(self.style.SUCCESS("✓ Stock inventory transformation completed successfully"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Transformation failed: {str(e)}"))
            raise

        finally:
            spark.stop()
            self.stdout.write("Spark session stopped")
