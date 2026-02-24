from decimal import Decimal

from django.core.management.base import BaseCommand
from elasticsearch.helpers import bulk

from api.esconnection import ES_CLIENT
from api.indexes import CLEANED_FRAMEWORK_AGREEMENTS_INDEX_NAME
from api.logger import logger
from api.models import CleanedFrameworkAgreement


def _to_float(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        try:
            return float(value)
        except Exception:
            return None
    try:
        return float(value)
    except Exception:
        return None


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

    def handle(self, *args, **options):
        if ES_CLIENT is None:
            logger.error("Elasticsearch client not configured (ES_CLIENT is None).")
            return

        batch_size = options.get("batch_size", 500)

        logger.info("Indexing CleanedFrameworkAgreement rows into Elasticsearch")
        actions = []
        count = 0

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
                "price_per_unit": _to_float(row.get("price_per_unit")),
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

            action = {"_op_type": "index", "_index": CLEANED_FRAMEWORK_AGREEMENTS_INDEX_NAME, "_id": doc_id, **doc}
            actions.append(action)
            count += 1

            if len(actions) >= batch_size:
                created, errors = bulk(client=ES_CLIENT, actions=actions, chunk_size=batch_size)
                logger.info(f"Indexed {created} documents (batch)")
                if errors:
                    logger.error("Errors during bulk index: %s", errors)
                actions = []

        if actions:
            created, errors = bulk(client=ES_CLIENT, actions=actions, chunk_size=batch_size)
            logger.info(f"Indexed {created} documents (final)")
            if errors:
                logger.error("Errors during bulk index: %s", errors)

        logger.info(f"Bulk indexing complete. Total documents indexed (approx): {count}")
