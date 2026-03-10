from django.core.management.base import BaseCommand
from django.db.models import Sum
from elasticsearch.helpers import bulk

from api.esconnection import ES_CLIENT
from api.indexes import WAREHOUSE_INDEX_NAME
from api.logger import logger
from api.models import (
    DimInventoryTransactionLine,
    DimProduct,
    DimProductCategory,
    DimWarehouse,
)
from api.utils import derive_country_iso3, fetch_goadmin_maps, safe_str, to_float


class Command(BaseCommand):
    help = "Bulk-index warehouse × product aggregates into Elasticsearch"

    def add_arguments(self, parser):
        parser.add_argument(
            "--only-available",
            type=int,
            choices=(0, 1),
            default=1,
            help="Whether to only include lines with item_status_name 'Available' (default: 1)",
        )
        parser.add_argument("--batch-size", type=int, default=500, help="Bulk helper chunk size (default: 500)")

    def handle(self, *args, **options):
        if ES_CLIENT is None:
            logger.error("Elasticsearch client not configured (ES_CLIENT is None).")
            return

        only_available = options.get("only_available", 1) == 1
        batch_size = options.get("batch_size", 500)

        logger.info("Building lookup tables for products, warehouses and categories")

        warehouses = DimWarehouse.objects.all().values("id", "name", "country")
        # Build warehouse lookup; store raw country field and warehouse id for later iso2->iso3 fallback
        wh_by_id = {
            str(w["id"]): {
                "warehouse_name": safe_str(w.get("name")),
                "country_iso3_raw": safe_str(w.get("country")).upper(),  # may be empty
                "warehouse_id_raw": safe_str(w.get("id")),
            }
            for w in warehouses
        }

        products = DimProduct.objects.all().values(
            "id",
            "name",
            "unit_of_measure",
            "product_category",
        )
        prod_by_id = {
            str(p["id"]): {
                "item_number": safe_str(p.get("id")),
                "item_name": safe_str(p.get("name")),
                "unit": safe_str(p.get("unit_of_measure")),
                "product_category_code": safe_str(p.get("product_category")),
            }
            for p in products
        }

        categories = DimProductCategory.objects.all().values("category_code", "name")
        cat_by_code = {str(c["category_code"]): safe_str(c.get("name")) for c in categories}

        iso2_to_iso3, iso3_to_country_name, iso3_to_region_name = fetch_goadmin_maps()

        logger.info("Querying transaction lines and aggregating by warehouse+product")
        q = DimInventoryTransactionLine.objects.all()
        if only_available:
            q = q.filter(item_status_name="Available")

        agg = q.values("warehouse", "product", "item_status_name").annotate(quantity=Sum("quantity"))

        actions = []
        count = 0
        for row in agg.iterator():
            warehouse_id = safe_str(row.get("warehouse"))
            product_id = safe_str(row.get("product"))

            wh = wh_by_id.get(warehouse_id)
            prod = prod_by_id.get(product_id)
            if not wh or not prod:
                continue

            qty_num = to_float(row.get("quantity"))

            status_val = safe_str(row.get("item_status_name"))
            # include status in doc id to avoid collisions when multiple statuses exist
            doc_id = f"{warehouse_id}__{product_id}__{status_val}"

            country_iso3 = derive_country_iso3(
                wh.get("warehouse_id_raw") or "",
                iso2_to_iso3,
                wh.get("country_iso3_raw") or "",
            )

            doc = {
                "id": doc_id,
                "warehouse_id": warehouse_id,
                "warehouse_name": wh.get("warehouse_name", ""),
                "country_iso3": country_iso3,
                "country_name": iso3_to_country_name.get(country_iso3.upper(), "") if country_iso3 else "",
                "region": iso3_to_region_name.get(country_iso3.upper(), "") if country_iso3 else "",
                "product_id": product_id,
                "item_number": prod.get("item_number", ""),
                "item_name": prod.get("item_name", ""),
                "unit": prod.get("unit", ""),
                "item_group": cat_by_code.get(prod.get("product_category_code", ""), ""),
                "item_status_name": status_val,
                "quantity": qty_num,
            }

            action = {"_op_type": "index", "_index": WAREHOUSE_INDEX_NAME, "_id": doc_id, **doc}
            actions.append(action)
            count += 1

            # Flush periodically to save memory
            if len(actions) >= batch_size:
                created, errors = bulk(client=ES_CLIENT, actions=actions, chunk_size=batch_size)
                logger.info(f"Indexed {created} documents (batch)")
                if errors:
                    logger.error("Errors during bulk index: %s", errors)
                actions = []

        # Final flush
        if actions:
            created, errors = bulk(client=ES_CLIENT, actions=actions, chunk_size=batch_size)
            logger.info(f"Indexed {created} documents (final)")
            if errors:
                logger.error("Errors during bulk index: %s", errors)

        logger.info(f"Bulk indexing complete. Total documents indexed (approx): {count}")
