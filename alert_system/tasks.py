import logging

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.db import transaction
from django.utils import timezone

from alert_system.mappings import CONNECTOR_REGISTRY

from .models import Connector, StacItems
from .utils import copy_to_eligible

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, retry_backoff=True)
def process_connector_task(self, connector_id):
    """
    Celery task to run ETL for one connector.
    """
    connector = Connector.objects.get(id=connector_id)
    connector.status = Connector.Status.RUNNING
    connector.save(update_fields=["status"])
    connector_class = CONNECTOR_REGISTRY[connector.type]
    extraction_class = connector_class.extractor
    connector_label = connector.ConnectorType(connector.type).label

    try:
        logger.info(f"[ETL] Starting connector: {connector_label}")

        # Run ETL inside a transaction
        with transaction.atomic():
            processor = extraction_class(connector)
            processor.run()

            connector.status = Connector.Status.SUCCESS
            connector.last_success_run = timezone.now()
            connector.save(update_fields=["status", "last_success_run"])

        logger.info(f"[ETL] Completed connector: {connector_label}")

    except Exception as exc:
        logger.exception(f"[ETL] Connector {connector.id} failed: {exc}")
        connector.status = Connector.Status.FAILED
        connector.save(update_fields=["status"])

        try:
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            logger.error(f"[ETL] Max retries exceeded for connector {connector.id}")
            raise


@shared_task
def validate_and_copy_items(connector_id):
    """
    Validate and copy unprocessed STAC items to EligibleItems.

    """
    try:
        connector = Connector.objects.get(id=connector_id)
    except Connector.DoesNotExist:
        logger.error(f"Connector {connector_id} does not exist")
        return {"error": "Connector not found", "connector_id": connector_id}
    connector_class = CONNECTOR_REGISTRY[connector.type]
    filter_class = connector_class.filter
    if not filter_class:
        logger.error(f"No filter class found for connector type: {connector.type}")
        return {"error": "Invalid connector type", "connector_id": connector_id}

    items = StacItems.objects.filter(connector=connector, processed=False).select_related("connector")

    processed_count = 0
    eligible_count = 0
    error_count = 0

    for item in items:
        try:
            with transaction.atomic():
                filter_obj = filter_class(item)

                if filter_obj.is_eligible():
                    copy_to_eligible(item)
                    eligible_count += 1

                item.processed = True
                item.save(update_fields=["processed"])
                processed_count += 1

        except Exception as e:
            error_count += 1
            logger.error(f"Error processing item {item.stac_id} for connector {connector_id}: {str(e)}", exc_info=True)
            # Continue processing other items
            continue

    result = {
        "connector_id": connector_id,
        "processed": processed_count,
        "eligible": eligible_count,
        "errors": error_count,
    }

    logger.info(f"Validation complete for connector {connector_id}: {result}")
    return result


@shared_task
def validate_all_connectors():
    """
    Trigger validation for all connectors.
    """
    connector_ids = Connector.objects.values_list("id", flat=True)

    if not connector_ids:
        logger.warning("No connectors found to validate")
        return {"message": "No connectors found"}

    tasks_queued = 0
    for connector_id in connector_ids:
        validate_and_copy_items.delay(connector_id)
        tasks_queued += 1

    logger.info(f"Queued {tasks_queued} validation tasks")
    return {"tasks_queued": tasks_queued, "connector_ids": list(connector_ids)}
