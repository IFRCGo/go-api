from django.core.management.base import BaseCommand
from elasticsearch.client import IndicesClient
from elasticsearch.helpers import bulk

from api.esaliashelper import create_versioned_index, get_alias_targets, swap_alias
from api.esconnection import ES_CLIENT
from api.indexes import (
    CLEANED_FRAMEWORK_AGREEMENTS_INDEX_NAME,
    CLEANED_FRAMEWORK_AGREEMENTS_MAPPING,
    CLEANED_FRAMEWORK_AGREEMENTS_SETTINGS,
)
from api.logger import logger
from api.models import CleanedFrameworkAgreement
from api.utils import to_float


def _to_iso(value):
    if value is None:
        return None
    try:
        return value.isoformat()
    except Exception:
        return None


class Command(BaseCommand):
    help = "Bulk-index cleaned framework agreements into Elasticsearch"

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

        # ------------------------------------------------------------------ #
        # Resolve the current alias targets BEFORE creating the new index so  #
        # we know which indexes to remove during the atomic swap later.        #
        # ------------------------------------------------------------------ #
        alias_name = CLEANED_FRAMEWORK_AGREEMENTS_INDEX_NAME  # alias the application queries
        indices_client = IndicesClient(client=ES_CLIENT)
        old_indexes = get_alias_targets(indices_client, alias_name)

        logger.info("Creating versioned index for alias '%s' (previous: %s)", alias_name, old_indexes or "none")
        versioned_index = create_versioned_index(
            es_client=ES_CLIENT,
            alias_name=alias_name,
            settings=CLEANED_FRAMEWORK_AGREEMENTS_SETTINGS,
            mapping=CLEANED_FRAMEWORK_AGREEMENTS_MAPPING,
        )
        logger.info("Versioned index '%s' created", versioned_index)

        logger.info("Indexing CleanedFrameworkAgreement rows into Elasticsearch")
        actions = []
        count = 0
        had_bulk_errors = False

        qs = CleanedFrameworkAgreement.objects.all().values(
            "id",
            "agreement_id",
            "classification",
            "default_agreement_line_effective_date",
            "default_agreement_line_expiration_date",
            "workflow_status",
            "status",
            "price_per_unit",
            "pa_line_procurement_category",
            "vendor_name",
            "vendor_valid_from",
            "vendor_valid_to",
            "vendor_country",
            "region_countries_covered",
            "item_type",
            "item_category",
            "item_service_short_description",
            "owner",
            "created_at",
            "updated_at",
        )

        for row in qs.iterator():
            doc_id = row.get("id")
            doc = {
                "id": row.get("id"),
                "agreement_id": row.get("agreement_id"),
                "classification": row.get("classification"),
                "default_agreement_line_effective_date": _to_iso(row.get("default_agreement_line_effective_date")),
                "default_agreement_line_expiration_date": _to_iso(row.get("default_agreement_line_expiration_date")),
                "workflow_status": row.get("workflow_status"),
                "status": row.get("status"),
                "price_per_unit": to_float(row.get("price_per_unit")),
                "pa_line_procurement_category": row.get("pa_line_procurement_category"),
                "vendor_name": row.get("vendor_name"),
                "vendor_valid_from": _to_iso(row.get("vendor_valid_from")),
                "vendor_valid_to": _to_iso(row.get("vendor_valid_to")),
                "vendor_country": row.get("vendor_country"),
                "region_countries_covered": row.get("region_countries_covered"),
                "item_type": row.get("item_type"),
                "item_category": row.get("item_category"),
                "item_service_short_description": row.get("item_service_short_description"),
                "owner": row.get("owner"),
                "created_at": _to_iso(row.get("created_at")),
                "updated_at": _to_iso(row.get("updated_at")),
            }

            action = {"_op_type": "index", "_index": versioned_index, "_id": doc_id, **doc}
            actions.append(action)
            count += 1

            if len(actions) >= batch_size:
                created, errors = bulk(client=ES_CLIENT, actions=actions, chunk_size=batch_size)
                logger.info(f"Indexed {created} documents (batch)")
                if errors:
                    logger.error("Errors during bulk index: %s", errors)
                    had_bulk_errors = True
                actions = []

        if actions:
            created, errors = bulk(client=ES_CLIENT, actions=actions, chunk_size=batch_size)
            logger.info(f"Indexed {created} documents (final)")
            if errors:
                logger.error("Errors during bulk index: %s", errors)
                had_bulk_errors = True

        logger.info(f"Bulk indexing complete. Total documents indexed (approx): {count}")

        if had_bulk_errors:
            raise RuntimeError(
                f"Bulk indexing for alias '{alias_name}' completed with errors. "
                "Alias swap aborted to preserve the existing index."
            )

        # ------------------------------------------------------------------ #
        # Atomically swap the alias from old index(es) to the new one.        #
        # ------------------------------------------------------------------ #
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
