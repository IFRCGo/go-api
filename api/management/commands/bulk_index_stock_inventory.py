from django.core.management.base import BaseCommand
from elasticsearch.client import IndicesClient
from elasticsearch.helpers import bulk

from api.esaliashelper import create_versioned_index, get_alias_targets, swap_alias
from api.esconnection import ES_CLIENT
from api.indexes import (
    STOCK_INVENTORY_INDEX_NAME,
    STOCK_INVENTORY_MAPPING,
    STOCK_INVENTORY_SETTINGS,
)
from api.logger import logger
from api.models import StockInventory
from api.utils import derive_country_iso3, fetch_goadmin_maps


class Command(BaseCommand):
    help = "Bulk-index StockInventory rows into Elasticsearch"

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=500, help="Bulk helper chunk size (default: 500)")
        parser.add_argument(
            "--delete-old",
            type=int,
            choices=(0, 1),
            default=0,
            help="Delete the previous index after a successful alias swap (default: 0)",
        )

    def handle(self, *args, **options):
        if ES_CLIENT is None:
            logger.error("Elasticsearch client not configured (ES_CLIENT is None).")
            return

        batch_size = options.get("batch_size", 500)
        delete_old = options.get("delete_old", 0) == 1

        alias_name = STOCK_INVENTORY_INDEX_NAME
        indices_client = IndicesClient(client=ES_CLIENT)
        old_indexes = get_alias_targets(indices_client, alias_name)

        logger.info("Creating versioned index for alias '%s' (previous: %s)", alias_name, old_indexes or "none")
        versioned_index = create_versioned_index(
            es_client=ES_CLIENT,
            alias_name=alias_name,
            settings=STOCK_INVENTORY_SETTINGS,
            mapping=STOCK_INVENTORY_MAPPING,
        )
        logger.info("Versioned index '%s' created", versioned_index)

        # Fetch country mapping once
        try:
            iso2_to_iso3, iso3_to_country_name, _ = fetch_goadmin_maps()
        except Exception:
            iso2_to_iso3, iso3_to_country_name = {}, {}

        logger.info("Indexing StockInventory rows into Elasticsearch")
        actions = []
        count = 0
        had_bulk_errors = False

        qs = StockInventory.objects.all().values(
            "id",
            "warehouse_id",
            "warehouse",
            "warehouse_country",
            "region",
            "product_category",
            "item_name",
            "quantity",
            "unit_measurement",
            "catalogue_link",
        )

        for row in qs.iterator():
            doc_id = row["id"]
            warehouse_id = row.get("warehouse_id") or ""
            country_iso3 = derive_country_iso3(warehouse_id, iso2_to_iso3, "")
            country_name = iso3_to_country_name.get(country_iso3, "") if country_iso3 else row.get("warehouse_country") or ""

            qty = row.get("quantity")
            doc = {
                "id": doc_id,
                "warehouse_id": warehouse_id,
                "warehouse": row.get("warehouse"),
                "warehouse_country": row.get("warehouse_country"),
                "country_iso3": country_iso3,
                "country": country_name,
                "region": row.get("region"),
                "product_category": row.get("product_category"),
                "item_name": row.get("item_name"),
                "quantity": float(qty) if qty is not None else None,
                "unit_measurement": row.get("unit_measurement"),
                "catalogue_link": row.get("catalogue_link"),
            }

            action = {"_op_type": "index", "_index": versioned_index, "_id": doc_id, **doc}
            actions.append(action)
            count += 1

            if len(actions) >= batch_size:
                created, errors = bulk(client=ES_CLIENT, actions=actions, chunk_size=batch_size)
                logger.info("Indexed %d documents (batch)", created)
                if errors:
                    logger.error("Errors during bulk index: %s", errors)
                    had_bulk_errors = True
                actions = []

        if actions:
            created, errors = bulk(client=ES_CLIENT, actions=actions, chunk_size=batch_size)
            logger.info("Indexed %d documents (final)", created)
            if errors:
                logger.error("Errors during bulk index: %s", errors)
                had_bulk_errors = True

        logger.info("Bulk indexing complete. Total documents indexed (approx): %d", count)

        if had_bulk_errors:
            raise RuntimeError(
                f"Bulk indexing for alias '{alias_name}' completed with errors. "
                "Alias swap aborted to preserve the existing index."
            )

        logger.info("Swapping alias '%s' -> '%s'", alias_name, versioned_index)
        swap_alias(
            indices_client=indices_client,
            alias_name=alias_name,
            new_index=versioned_index,
            old_indexes=old_indexes,
        )
        logger.info("Alias '%s' now points to '%s'", alias_name, versioned_index)

        if delete_old and old_indexes:
            for old_idx in old_indexes:
                if old_idx != versioned_index:
                    logger.info("Deleting old index '%s'", old_idx)
                    indices_client.delete(index=old_idx)
