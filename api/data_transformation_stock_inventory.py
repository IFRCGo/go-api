"""
Stock Inventory Data Transformation using PySpark

This script loads warehouse inventory data from Postgres, applies business logic
filters, joins with mapping tables, and writes the cleaned stock inventory to the
database.

Usage:
    # As a standalone script (requires Django environment)
    python api/data_transformation_stock_inventory.py

    # As a Django management command (recommended)
    docker compose run --rm serve python manage.py transform_stock_inventory
    docker compose run --rm serve python manage.py transform_stock_inventory --dry-run
    docker compose run --rm serve python manage.py transform_stock_inventory --limit 100
    docker compose run --rm serve python manage.py transform_stock_inventory --export-csv stock_inventory.csv
    docker compose run --rm serve python manage.py transform_stock_inventory --warehouse-ids AE1DUB002,AR1BUE002
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional
from urllib.request import urlretrieve

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import StringType, StructField, StructType

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION - Edit these warehouse codes as needed
# ============================================================================

DEFAULT_WAREHOUSE_CODES = [
    "AE1DUB002",  # Dubai
    "AR1BUE002",  # Buenos Aires
    "AU1BRI003",  # Brisbane
    "ES1LAS001",  # Las Palmas
    "GT1GUA001",  # Guatemala
    "HN1COM002",  # Comayagua
    "MY1SEL001",  # Selangor
    "PA1ARR001",  # Arraijan
    "TR1ISTA02",  # Istanbul
]

TRANSACTION_STATUSES = [
    "Deducted",
    "Purchased",
    "Received",
    "Reserved physical",
    "Sold",
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_jdbc_config() -> dict:
    """Get JDBC connection configuration from environment variables.

    Retrieves PostgreSQL connection parameters from Django environment variables
    and constructs a JDBC connection string.

    Returns:
        dict: Dictionary containing JDBC connection parameters including:
            - host: PostgreSQL host (default: 'db')
            - port: PostgreSQL port (default: '5432')
            - database: Database name
            - user: Database username
            - password: Database password
            - url: Complete JDBC connection URL

    Raises:
        KeyError: If required environment variables (DJANGO_DB_NAME, DJANGO_DB_USER,
                  DJANGO_DB_PASS) are not set.
    """
    return {
        "host": os.getenv("DJANGO_DB_HOST", "db"),
        "port": os.getenv("DJANGO_DB_PORT", "5432"),
        "database": os.environ["DJANGO_DB_NAME"],
        "user": os.environ["DJANGO_DB_USER"],
        "password": os.environ["DJANGO_DB_PASS"],
        "url": (
            f"jdbc:postgresql://{os.getenv('DJANGO_DB_HOST', 'db')}:"
            f"{os.getenv('DJANGO_DB_PORT', '5432')}/{os.environ['DJANGO_DB_NAME']}"
        ),
    }


def create_spark_session(app_name: str = "stock-inventory-transformation") -> SparkSession:
    """Create and configure a Spark session with PostgreSQL JDBC driver.

    Downloads the PostgreSQL JDBC driver if not already present and creates a
    configured Spark session with adaptive execution enabled.

    Args:
        app_name: Name for the Spark application (default: 'stock-inventory-transformation')

    Returns:
        SparkSession: Configured Spark session with PostgreSQL JDBC driver loaded

    Raises:
        URLError: If JDBC driver download fails
        Exception: If Spark session creation fails
    """
    logger.info("Creating Spark session...")

    # Download PostgreSQL JDBC driver if not present
    postgres_jdbc_version = "42.7.4"
    postgres_jdbc_jar = Path(f"/tmp/postgresql-{postgres_jdbc_version}.jar")
    postgres_jdbc_url = (
        "https://repo1.maven.org/maven2/org/postgresql/postgresql/"
        f"{postgres_jdbc_version}/postgresql-{postgres_jdbc_version}.jar"
    )

    if not postgres_jdbc_jar.exists():
        logger.info(f"Downloading PostgreSQL JDBC driver version {postgres_jdbc_version}...")
        urlretrieve(postgres_jdbc_url, postgres_jdbc_jar)
        logger.info(f"  ✓ JDBC driver downloaded to {postgres_jdbc_jar}")
    else:
        logger.info(f"  ✓ Using existing JDBC driver at {postgres_jdbc_jar}")

    spark_master = os.getenv("SPARK_MASTER", "local[*]")

    spark = (
        SparkSession.builder.appName(app_name)
        .master(spark_master)
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.jars", str(postgres_jdbc_jar))
        .getOrCreate()
    )

    logger.info(f"✓ Spark session created (master: {spark_master})")
    return spark


def load_jdbc_table(spark: SparkSession, jdbc_config: dict, table_name: str) -> DataFrame:
    """Load a single table from Postgres via JDBC.

    Connects to PostgreSQL database and loads the specified table as a Spark DataFrame.

    Args:
        spark: Active Spark session
        jdbc_config: JDBC connection configuration dictionary (from get_jdbc_config())
        table_name: Name of the PostgreSQL table to load

    Returns:
        DataFrame: Spark DataFrame containing the table data

    Raises:
        Py4JJavaError: If JDBC connection fails or table doesn't exist
    """
    return (
        spark.read.format("jdbc")
        .option("url", jdbc_config["url"])
        .option("dbtable", table_name)
        .option("user", jdbc_config["user"])
        .option("password", jdbc_config["password"])
        .option("driver", "org.postgresql.Driver")
        .load()
    )


# ============================================================================
# MAIN TRANSFORMATION FUNCTIONS
# ============================================================================


def load_dimension_tables(spark: SparkSession) -> dict[str, DataFrame]:
    """Load all required dimension tables from Postgres.

    Loads the following dimension tables via JDBC:
        - dimwarehouse: Warehouse location and metadata
        - dimproduct: Product catalog information
        - diminventorytransactionline: Individual transaction line items
        - diminventorytransaction: Transaction headers
        - dimproductcategory: Product category classifications

    Args:
        spark: Active Spark session

    Returns:
        dict[str, DataFrame]: Dictionary mapping table names to their DataFrames

    Raises:
        Py4JJavaError: If any table cannot be loaded from database
        KeyError: If JDBC configuration is invalid
    """
    logger.info("Loading dimension tables from Postgres...")

    jdbc_config = get_jdbc_config()

    tables = {
        "dimwarehouse": "api_dimwarehouse",
        "dimproduct": "api_dimproduct",
        "diminventorytransactionline": "api_diminventorytransactionline",
        "diminventorytransaction": "api_diminventorytransaction",
        "dimproductcategory": "api_dimproductcategory",
    }

    dataframes = {}
    for name, table in tables.items():
        df = load_jdbc_table(spark, jdbc_config, table)
        dataframes[name] = df
        logger.info(f"  ✓ {name} loaded")

    logger.info("✓ All dimension tables loaded successfully")
    return dataframes


def register_temp_views(dataframes: dict[str, DataFrame]) -> None:
    """Register all DataFrames as temporary SQL views.

    Creates temporary SQL views for each DataFrame to enable SQL-based transformations.
    Views are session-scoped and exist only for the duration of the Spark session.

    Args:
        dataframes: Dictionary mapping view names to DataFrames

    Returns:
        None

    Raises:
        AnalysisException: If view creation fails
    """
    logger.info("Registering temporary SQL views...")

    for name, df in dataframes.items():
        df.createOrReplaceTempView(name)
        logger.info(f"  ✓ Registered view: {name}")

    logger.info("✓ All views registered")


def apply_transaction_filters(spark: SparkSession) -> None:
    """Apply business logic filters to transaction tables.

    Filters the diminventorytransaction table to exclude weighted average inventory
    closings and transactions marked as excluded from inventory value.

    Args:
        spark: Active Spark session with diminventorytransaction view registered

    Returns:
        None: Updates the diminventorytransaction temp view in-place

    Raises:
        AnalysisException: If diminventorytransaction view doesn't exist
    """
    logger.info("Applying transaction filters...")

    # Filter diminventorytransaction
    logger.info("  - Filtering inventory transactions (excluding weighted average closings)")
    filtered_transactions = spark.sql(
        """
        SELECT *
        FROM diminventorytransaction
                WHERE COALESCE(reference_category, '') NOT ILIKE '%Weighted average inventory closing%'
                    AND excluded_from_inventory_value IS NOT TRUE
        ORDER BY id
    """
    )
    filtered_count = filtered_transactions.count()
    filtered_transactions.createOrReplaceTempView("diminventorytransaction")
    logger.info(f"    ✓ {filtered_count:,} transactions after filter")


def apply_warehouse_filter(spark: SparkSession, warehouse_codes: list[str]) -> None:
    """Filter warehouses to specific codes.

    Restricts the warehouse dimension to only the specified warehouse IDs.
    This is used to limit the scope of the inventory analysis to specific
    regional warehouses.

    Args:
        spark: Active Spark session with dimwarehouse view registered
        warehouse_codes: List of warehouse ID codes to include (e.g., ['AE1DUB002', 'ES1LAS001'])

    Returns:
        None: Updates the dimwarehouse temp view in-place

    Raises:
        AnalysisException: If dimwarehouse view doesn't exist
        ValueError: If warehouse_codes list is empty
    """
    if not warehouse_codes:
        raise ValueError("warehouse_codes cannot be empty")

    logger.info(f"Filtering to {len(warehouse_codes)} specific warehouses...")

    filtered_warehouses = spark.table("dimwarehouse").filter(col("id").isin(warehouse_codes))

    filtered_count = filtered_warehouses.count()
    filtered_warehouses.createOrReplaceTempView("dimwarehouse")

    logger.info(f"  ✓ Filtered to {filtered_count} warehouses: {', '.join(warehouse_codes)}")


def apply_transaction_line_filters(spark: SparkSession) -> None:
    """Apply filters to inventory transaction lines.

    Filters transaction lines to exclude IFRC-owned items, include only specific
    transaction statuses, ensure item status is 'OK', and exclude returned items.

    Business Rules:
        - Exclude items where owner contains '#ifrc'
        - Include only statuses: Deducted, Purchased, Received, Reserved physical, Sold
        - Include only items with status = 'OK'
        - Exclude items with returned packing slips

    Args:
        spark: Active Spark session with diminventorytransactionline view registered

    Returns:
        None: Updates the diminventorytransactionline temp view in-place

    Raises:
        AnalysisException: If diminventorytransactionline view doesn't exist
    """
    logger.info("Applying transaction line filters...")
    logger.info("  - Excluding IFRC-owned items")
    logger.info(f"  - Including only statuses: {', '.join(TRANSACTION_STATUSES)}")
    logger.info("  - Including only 'OK' item status")
    logger.info("  - Excluding returned packing slips")

    statuses_sql = ", ".join(f"'{status}'" for status in TRANSACTION_STATUSES)

    filtered_lines = spark.sql(
        f"""
        SELECT *
        FROM diminventorytransactionline
                WHERE COALESCE(owner, '') NOT ILIKE '%#ifrc%'
          AND status IN ({statuses_sql})
          AND item_status = 'OK'
                    AND packing_slip_returned IS NOT TRUE
    """
    )

    filtered_count = filtered_lines.count()
    filtered_lines.createOrReplaceTempView("diminventorytransactionline")
    logger.info(f"  ✓ {filtered_count:,} transaction lines after filters")


def apply_product_category_filters(spark: SparkSession) -> None:
    """Filter out product categories (e.g., services).

    Excludes product categories classified as 'services' from the inventory,
    retaining only physical goods.

    Args:
        spark: Active Spark session with dimproductcategory view registered

    Returns:
        None: Updates the dimproductcategory temp view in-place

    Raises:
        AnalysisException: If dimproductcategory view doesn't exist
    """
    logger.info("Applying product category filters...")
    logger.info("  - Excluding 'services' category")

    filtered_categories = spark.sql(
        """
        SELECT *
        FROM dimproductcategory
        WHERE COALESCE(name, '') NOT ILIKE 'services'
    """
    )

    filtered_count = filtered_categories.count()
    filtered_categories.createOrReplaceTempView("dimproductcategory")
    logger.info(f"  ✓ {filtered_count:,} product categories after filter")


def load_country_region_mapping(spark: SparkSession) -> None:
    """Load ISO country to region mappings from the framework agreement module.

    Imports and executes the get_country_region_mapping function from the framework
    agreement transformation module to fetch ISO2, ISO3, country name, and region data.
    Registers the result as 'isomapping' temp view.

    Args:
        spark: Active Spark session

    Returns:
        None: Creates 'isomapping' temp view in Spark session

    Raises:
        ImportError: If framework agreement module cannot be imported
        Exception: If country/region mapping retrieval fails
    """
    logger.info("Loading country/region mapping...")

    # Import here to avoid circular dependency and ensure Django is ready
    from api.data_transformation_framework_agreement import get_country_region_mapping

    mapping_df = get_country_region_mapping(spark)
    mapping_count = mapping_df.count()
    mapping_df.createOrReplaceTempView("isomapping")

    logger.info(f"  ✓ Loaded {mapping_count:,} country/region mappings")


def load_item_catalogue_mapping(spark: SparkSession) -> None:
    """Load item code to catalogue URL mappings from Django model.

    Queries the ItemCodeMapping Django model to retrieve product codes and their
    corresponding catalog URLs, then creates a Spark DataFrame and registers it
    as 'itemcatalogue' temp view.

    Args:
        spark: Active Spark session

    Returns:
        None: Creates 'itemcatalogue' temp view in Spark session

    Raises:
        ImportError: If Django models cannot be imported
        OperationalError: If database query fails
    """
    logger.info("Loading item catalogue mappings...")

    # Import here to ensure Django is ready
    from api.models import ItemCodeMapping

    # Allow sync Django ORM calls
    os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

    rows = list(ItemCodeMapping.objects.exclude(code__isnull=True).exclude(url__isnull=True).values("code", "url"))

    schema = StructType(
        [
            StructField("code", StringType(), True),
            StructField("url", StringType(), True),
        ]
    )

    item_mapping_df = spark.createDataFrame(rows, schema=schema)
    item_count = item_mapping_df.count()
    item_mapping_df.createOrReplaceTempView("itemcatalogue")

    logger.info(f"  ✓ Loaded {item_count:,} item catalogue mappings")


def build_stock_inventory_dataframe(spark: SparkSession, limit: Optional[int] = None) -> DataFrame:
    """Build the final stock inventory DataFrame using SQL joins and aggregation.

    Executes a complex SQL query that:
        1. Joins warehouse, transaction, product, and category dimensions
        2. Performs left joins with country/region and catalogue mappings
        3. Aggregates quantities by warehouse, product, and category
        4. Filters to positive quantities only
        5. Orders results by warehouse, category, and quantity

    Output Columns:
        - warehouse_id: Warehouse identifier code
        - warehouse: Warehouse name
        - warehouse_country: Country where warehouse is located
        - region: Geographical region
        - product_category: Product category name
        - item_name: Product name
        - quantity: Aggregated quantity (rounded to 2 decimal places)
        - unit_measurement: Unit of measure (lowercase)
        - catalogue_link: URL to product catalogue (nullable)

    Args:
        spark: Active Spark session with all required temp views registered
        limit: Optional row limit for testing/dry-run (default: None for no limit)

    Returns:
        DataFrame: Final stock inventory DataFrame with aggregated results

    Raises:
        AnalysisException: If any required temp view doesn't exist
        Exception: If SQL execution fails
    """
    logger.info("Building final stock inventory DataFrame...")

    limit_clause = f"LIMIT {limit}" if limit else ""

    result_df = spark.sql(
        f"""
        SELECT
            w.id AS warehouse_id,
            w.name AS warehouse,
            COALESCE(im.country_name, w.country) AS warehouse_country,
            im.region AS region,
            pc.name AS product_category,
            p.name AS item_name,
            CAST(ROUND(SUM(quantity), 2) AS DECIMAL(18,2)) AS quantity,
            LOWER(p.unit_of_measure) AS unit_measurement,
            ic.url AS catalogue_link
        FROM dimwarehouse w
        JOIN diminventorytransactionline itl
            ON w.id = itl.warehouse
        JOIN diminventorytransaction it
            ON itl.inventory_transaction = it.id
        JOIN dimproduct p
            ON itl.product = p.id
        JOIN dimproductcategory pc
            ON p.product_category = pc.category_code
        LEFT JOIN isomapping im
            ON w.country = im.iso3
        LEFT JOIN itemcatalogue ic
            ON p.id = ic.code
        GROUP BY
            w.name,
            w.id,
            COALESCE(im.country_name, w.country),
            im.region,
            pc.name,
            p.name,
            LOWER(p.unit_of_measure),
            ic.url
        HAVING quantity > 0
        ORDER BY warehouse, product_category, quantity DESC
        {limit_clause}
    """
    )

    result_count = result_df.count()
    logger.info(f"  ✓ Generated {result_count:,} stock inventory records")

    return result_df


def write_to_database(df: DataFrame, dry_run: bool = False) -> None:
    """Write the stock inventory DataFrame to the database.

    Writes the stock inventory data to the api_stockinventory table in PostgreSQL.
    In dry-run mode, displays sample data without performing the write operation.
    Uses a truncate + append strategy to preserve the Django-managed table schema,
    indexes, and constraints.

    Args:
        df: Stock inventory DataFrame to write
        dry_run: If True, displays 20 sample rows without writing to database

    Returns:
        None

    Raises:
        Py4JJavaError: If JDBC write operation fails
        KeyError: If JDBC configuration is missing required parameters
    """
    if dry_run:
        logger.info("DRY RUN MODE - Showing sample data (not writing to database):")
        df.show(20, truncate=False)
        logger.info("✓ Dry run complete (no data written)")
        return

    logger.info("Writing stock inventory to database (api_stockinventory table)...")

    jdbc_config = get_jdbc_config()

    # Keep the migration-defined table structure intact by truncating rows first,
    # then writing with append mode instead of JDBC overwrite.
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE api_stockinventory RESTART IDENTITY")

    df.write.format("jdbc").option("url", jdbc_config["url"]).option("dbtable", "api_stockinventory").option(
        "user", jdbc_config["user"]
    ).option("password", jdbc_config["password"]).option("driver", "org.postgresql.Driver").mode("append").save()

    logger.info("✓ Stock inventory successfully written to database")


def verify_and_display_results(spark: SparkSession, num_rows: int = 20) -> None:
    """Retrieve and display the stock inventory table for verification.

    Reads the api_stockinventory table from the database and displays a sample
    of rows to verify the transformation results. Shows total row count and
    displays data without truncation.

    Args:
        spark: Active Spark session
        num_rows: Number of rows to display (default: 20)

    Returns:
        None

    Raises:
        Py4JJavaError: If table read operation fails
        Exception: If verification process encounters an error
    """
    logger.info(f"Retrieving and displaying {num_rows} rows from api_stockinventory table for verification...")

    jdbc_config = get_jdbc_config()

    try:
        verification_df = load_jdbc_table(spark, jdbc_config, "api_stockinventory")
        total_count = verification_df.count()

        logger.info(f"✓ Total rows in api_stockinventory: {total_count:,}")
        logger.info(f"\nDisplaying first {num_rows} rows:")
        logger.info("=" * 120)

        verification_df.show(num_rows, truncate=False)

        logger.info("=" * 120)
        logger.info("✓ Verification complete")

    except Exception as e:
        logger.error(f"✗ Failed to retrieve verification data: {str(e)}")
        raise


def export_to_csv(spark: SparkSession, output_path: str = "stock_inventory.csv") -> None:
    """Export the stock inventory table to CSV file.

    Reads the api_stockinventory table from the database, converts it to a Pandas
    DataFrame, and exports it to a CSV file. This is useful for sharing data with
    external tools or performing additional analysis.

    Args:
        spark: Active Spark session
        output_path: Path where CSV file should be saved (default: stock_inventory.csv)

    Returns:
        None

    Raises:
        Py4JJavaError: If table read operation fails
        IOError: If CSV file cannot be written
        MemoryError: If dataset is too large to convert to Pandas
        Exception: If export process encounters an error
    """
    logger.info(f"Exporting stock inventory to CSV: {output_path}")

    jdbc_config = get_jdbc_config()

    try:
        # Load the table from database
        df = load_jdbc_table(spark, jdbc_config, "api_stockinventory")
        total_count = df.count()

        logger.info(f"  - Loading {total_count:,} rows from database...")

        # Convert to Pandas and export to CSV
        pandas_df = df.toPandas()
        pandas_df.to_csv(output_path, index=False)

        logger.info(f"✓ Successfully exported {total_count:,} rows to {output_path}")

    except Exception as e:
        logger.error(f"✗ Failed to export CSV: {str(e)}")
        raise


# ============================================================================
# MAIN ORCHESTRATION
# ============================================================================


def transform_stock_inventory(
    spark: SparkSession,
    warehouse_codes: Optional[list[str]] = None,
    dry_run: bool = False,
    limit: Optional[int] = None,
    export_csv: Optional[str] = None,
) -> DataFrame:
    """Main orchestration function for stock inventory transformation.

    Executes the complete ETL pipeline for warehouse stock inventory:
        1. Loads dimension tables from PostgreSQL
        2. Registers temporary SQL views
        3. Applies business logic filters (transactions, warehouses, products)
        4. Loads country/region and catalog mappings
        5. Builds final aggregated inventory DataFrame
        6. Writes results to database (unless dry-run)
        7. Displays verification results
        8. Optionally exports to CSV

    The transformation applies multiple filters:
        - Excludes weighted average inventory closings
        - Filters to specified warehouses
        - Excludes IFRC-owned items
        - Includes only specific transaction statuses
        - Excludes 'services' product category
        - Filters to 'OK' item status only

    Args:
        spark: Active Spark session with JDBC driver configured
        warehouse_codes: Optional list of warehouse codes to filter. If None, uses
                        DEFAULT_WAREHOUSE_CODES (9 default warehouses)
        dry_run: If True, shows results without writing to database. Skips verification
                and CSV export steps
        limit: Optional row limit for the final query. Useful for testing with smaller
               datasets
        export_csv: Optional file path for CSV export. If provided (and not dry-run),
                   exports the database table to CSV after transformation

    Returns:
        DataFrame: Final stock inventory DataFrame with columns:
            - warehouse_id, warehouse, warehouse_country, region,
            - product_category, item_name, quantity, unit_measurement, catalogue_link

    Raises:
        Py4JJavaError: If JDBC operations fail (connection, read, or write)
        AnalysisException: If SQL queries reference non-existent views or columns
        KeyError: If required environment variables are missing
        Exception: Any other error during transformation process

    Example:
        >>> spark = create_spark_session()
        >>> df = transform_stock_inventory(
        ...     spark,
        ...     warehouse_codes=['AE1DUB002', 'ES1LAS001'],
        ...     limit=100,
        ...     dry_run=True
        ... )
    """
    logger.info("=" * 80)
    logger.info("STOCK INVENTORY TRANSFORMATION STARTED")
    logger.info("=" * 80)

    if warehouse_codes is None:
        warehouse_codes = DEFAULT_WAREHOUSE_CODES

    try:
        # Step 1: Load dimension tables
        dataframes = load_dimension_tables(spark)

        # Step 2: Register SQL views
        register_temp_views(dataframes)

        # Step 3: Apply filters
        apply_transaction_filters(spark)
        apply_warehouse_filter(spark, warehouse_codes)
        apply_transaction_line_filters(spark)
        apply_product_category_filters(spark)

        # Step 4: Load mapping tables
        load_country_region_mapping(spark)
        load_item_catalogue_mapping(spark)

        # Step 5: Build final DataFrame
        result_df = build_stock_inventory_dataframe(spark, limit=limit)

        # Step 6: Write to database
        write_to_database(result_df, dry_run=dry_run)

        # Step 7: Verify results (unless dry run)
        if not dry_run:
            verify_and_display_results(spark, num_rows=20)

        # Step 8: Export to CSV if requested (unless dry run)
        if export_csv and not dry_run:
            export_to_csv(spark, output_path=export_csv)

        logger.info("=" * 80)
        logger.info("✓ STOCK INVENTORY TRANSFORMATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)

        return result_df

    except Exception as e:
        logger.error("=" * 80)
        logger.error("✗ STOCK INVENTORY TRANSFORMATION FAILED")
        logger.error("=" * 80)
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error("Check the logs above to identify which step failed.")
        raise


def main() -> None:
    """Main entry point for standalone script execution.

    Configures logging, initializes Django, creates a Spark session, and executes
    the stock inventory transformation. This function is called when the script
    is run directly (not as a Django management command).

    Returns:
        None

    Raises:
        Exception: Any exception from the transformation process is propagated
                   after proper cleanup (Spark session stop)
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Ensure Django is set up
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")
    import django

    django.setup()

    # Create Spark session
    spark = create_spark_session()

    try:
        transform_stock_inventory(spark)
    finally:
        logger.info("Stopping Spark session...")
        spark.stop()
        logger.info("✓ Spark session stopped")


if __name__ == "__main__":
    main()
