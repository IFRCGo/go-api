"""
Django management command for stock inventory transformation.

Usage:
    # Run full transformation
    docker compose run --rm serve python manage.py transform_stock_inventory

    # Dry run (show results without writing to database)
    docker compose run --rm serve python manage.py transform_stock_inventory --dry-run

    # Limit output rows (for testing)
    docker compose run --rm serve python manage.py transform_stock_inventory --limit 100

    # Use custom warehouse codes
    docker compose run --rm serve python manage.py transform_stock_inventory --warehouse-ids AE1DUB002,AR1BUE002,ES1LAS001

    # Export to CSV after transformation
    docker compose run --rm serve python manage.py transform_stock_inventory --export-csv stock_inventory.csv

    # Combine options
    docker compose run --rm serve python manage.py transform_stock_inventory --dry-run --limit 50 --warehouse-ids AE1DUB002
"""

import logging

from django.core.management.base import BaseCommand

from api.data_transformation_stock_inventory import (
    DEFAULT_WAREHOUSE_CODES,
    create_spark_session,
    transform_stock_inventory,
)


class Command(BaseCommand):
    help = "Transform and load stock inventory data using PySpark"

    def add_arguments(self, parser):
        """Add command-line arguments for the management command.

        Defines the following optional arguments:
            --dry-run: Run transformation without writing to database
            --limit: Limit number of output rows for testing
            --warehouse-ids: Comma-separated warehouse codes to filter
            --export-csv: Export results to CSV file

        Args:
            parser: Django command argument parser (argparse.ArgumentParser)

        Returns:
            None
        """
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
        parser.add_argument(
            "--export-csv",
            type=str,
            default=None,
            help="Export results to CSV file (e.g., 'stock_inventory.csv')",
        )

    def handle(self, *args, **options):
        """Execute the stock inventory transformation command.

        Main command handler that:
            1. Configures logging
            2. Parses and validates command-line options
            3. Creates Spark session with JDBC driver
            4. Executes the transformation pipeline
            5. Handles success/error reporting
            6. Ensures proper Spark session cleanup

        Args:
            *args: Positional arguments (unused)
            **options: Dictionary of command-line options including:
                - dry_run (bool): Whether to skip database write
                - limit (int or None): Row limit for output
                - warehouse_ids (str or None): Comma-separated warehouse codes
                - export_csv (str or None): CSV export file path

        Returns:
            None

        Raises:
            Exception: Re-raises any exception from transformation after logging it
        """
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
        export_csv = options.get("export_csv")

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
        if export_csv:
            if dry_run:
                self.stdout.write(self.style.WARNING("⚠️  CSV export will be skipped in dry-run mode"))
            else:
                self.stdout.write(f"📄 CSV will be exported to: {export_csv}")

        # Create Spark session (with JDBC driver download)
        spark = create_spark_session()

        try:
            # Run transformation
            transform_stock_inventory(
                spark,
                warehouse_codes=warehouse_codes,
                dry_run=dry_run,
                limit=limit,
                export_csv=export_csv,
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
