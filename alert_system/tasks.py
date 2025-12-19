import logging
import uuid

from celery import chain, group, shared_task
from celery.exceptions import MaxRetriesExceededError
from django.db import transaction

from api.models import Event

from .helpers import get_connector_processor, set_connector_status
from .models import Connector, LoadItem

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, retry_backoff=True)
def polling_task(self, connector_id):
    """
    Celery task to run ETL for one connector.
    """
    extraction_run_id = str(uuid.uuid4())
    processor, connector = get_connector_processor(connector_id)

    try:
        set_connector_status(connector, Connector.Status.RUNNING)
        logger.info(f"[ETL] Starting connector: {connector.id}")

        processor.run(extraction_run_id=extraction_run_id)

        set_connector_status(connector, Connector.Status.SUCCESS)
        logger.info(f"[ETL] Completed connector: {connector.id}")
        return extraction_run_id

    except Exception as exc:
        logger.exception(f"[ETL] Connector {connector.id} failed: {exc}")
        set_connector_status(connector, Connector.Status.FAILED)

        try:
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            logger.error(f"[ETL] Max retries exceeded for connector {connector.id}", exc_info=True)
            raise


@shared_task(bind=True, max_retries=3, retry_backoff=True)
def fetch_past_events_from_monty(self, extraction_run_id):
    """
    Fetch past events for all eligible items from a specific extraction run.
    This task is chained after process_connector_task.
    """
    if not extraction_run_id:
        logger.warning("No extraction_run_id provided, skipping past events fetch")
        return

    try:
        eligible_items = LoadItem.objects.filter(
            extraction_run_id=extraction_run_id,
            item_eligible=True,
            is_past_event=False,
        )

        count = eligible_items.count()

        if count == 0:
            logger.info(f"[Past Events] No eligible items in run {extraction_run_id}")
            return

        logger.info(f"[Past Events] Processing {count} items from run {extraction_run_id}")

        first_item = eligible_items.first()
        if not first_item:
            logger.info("No Connector found for the Event")
            return

        connector_id = first_item.connector.id

        processor, _ = get_connector_processor(connector_id)

        # Process each eligible item
        processed = 0
        failed = 0

        for load_obj in eligible_items.iterator():
            try:
                with transaction.atomic():
                    processor.fetch_past_events(load_obj)
                    processed += 1
            except Exception as e:
                failed += 1
                logger.error(f"[Past Events] Failed for item {load_obj.id} in run {extraction_run_id}: {e}", exc_info=True)
                # Continue processing other items
                continue

        logger.info(f"[Past Events] Completed run {extraction_run_id}: " f"{processed} processed, {failed} failed")

        return {"extraction_run_id": extraction_run_id, "processed": processed, "failed": failed, "total": count}

    except Exception as exc:
        logger.exception(f"[Past Events] Task failed for run {extraction_run_id}: {exc}")

        try:
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            logger.error(f"[Past Events] Max retries exceeded for run {extraction_run_id}", exc_info=True)
            raise


@shared_task(bind=True, max_retries=3, retry_backoff=True)
def fetch_past_events_from_go(self, extraction_run_id, connector_id):
    _, connector = get_connector_processor(connector_id=connector_id)
    eligible_items = LoadItem.objects.filter(
        extraction_run_id=extraction_run_id,
        item_eligible=True,
        is_past_event=False,
    ).only("id", "total_people_exposed")

    for item in eligible_items.iterator():
        go_event_ids = list(
            Event.objects.filter(field_reports__num_affected__gte=item.total_people_exposed, dtype=connector.dtype)
            .values_list("id", flat=True)
            .distinct()
        )

        item.related_go_events = go_event_ids
        item.save(update_fields=["related_go_events"])


@shared_task
def process_connector_task(connector_id):
    """
    Execute the full ETL pipeline:
    1. Process connector (main extraction)
    2. Fetch past events for eligible items
    """
    return chain(
        polling_task.s(connector_id), group(fetch_past_events_from_go.s(connector_id), fetch_past_events_from_monty.s())
    ).apply_async()
