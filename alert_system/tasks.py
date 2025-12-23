import logging
import uuid
from collections import defaultdict

from celery import chain, group, shared_task
from celery.exceptions import MaxRetriesExceededError
from django.db import transaction
from django.db.models import Max

from alert_system.etl.base.extraction import PastEventExtractionClass
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
        logger.info(f"[ETL] Starting connector: {connector}")

        processor.run(extraction_run_id=extraction_run_id)

        set_connector_status(connector, Connector.Status.SUCCESS)
        logger.info(f"[ETL] Completed connector: {connector}")
        return extraction_run_id

    except Exception as exc:
        logger.warning(f"[ETL] Connector {connector} failed", exc_info=True)
        set_connector_status(connector, Connector.Status.FAILED)

        try:
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            logger.error(f"[ETL] Max retries exceeded for connector {connector.type.label}", exc_info=True)
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
        eligible_items_qs = LoadItem.objects.filter(
            extraction_run_id=extraction_run_id,
            item_eligible=True,
            is_past_event=False,
        )

        count = eligible_items_qs.count()

        logger.info(f"[Past Events] Processing {count} items from run {extraction_run_id}")

        first_item = eligible_items_qs.first()
        if not first_item:
            logger.info("No Connector found for the Event")
            return

        connector_id = first_item.connector.id

        processor, _ = get_connector_processor(connector_id)
        past_event_extraction_service = PastEventExtractionClass(processor)

        # Process each eligible item
        processed = 0
        failed = 0

        for load_obj in eligible_items_qs.iterator():
            try:
                with transaction.atomic():
                    past_event_extraction_service.extract_past_events(load_obj=load_obj)
                    processed += 1
            except Exception as e:
                failed += 1
                logger.warning(f"[Past Events] Failed for item {load_obj.id} in run {extraction_run_id}: {e}", exc_info=True)
                # Continue processing other items
                continue

        logger.info(f"[Past Events] Completed run {extraction_run_id}: " f"{processed} processed, {failed} failed")

    except Exception as exc:
        logger.warning(f"[Past Events] Task failed for run {extraction_run_id}")

        try:
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            logger.warning(f"[Past Events] Max retries exceeded for run {extraction_run_id}", exc_info=True)
            raise


@shared_task(bind=True, max_retries=3, retry_backoff=True)
def fetch_past_events_from_go(self, extraction_run_id, connector_id):
    _, connector = get_connector_processor(connector_id=connector_id)
    items = list(
        LoadItem.objects.filter(
            extraction_run_id=extraction_run_id,
            item_eligible=True,
            is_past_event=False,
        ).only("id", "total_people_exposed", "country_codes")
    )

    min_people = min(i.total_people_exposed for i in items)
    all_countries = set().union(*(i.country_codes for i in items))

    # NOTE: Should we take the max or the latest field_report value?
    events = (
        Event.objects.filter(
            dtype=connector.dtype,
            countries__iso3__in=all_countries,
        )
        .annotate(max_affected=Max("field_reports__num_affected"))
        .filter(max_affected__gte=min_people)
        .distinct()
        .prefetch_related("countries")
    )

    events_by_country = defaultdict(list)

    for event in events:
        for country in event.countries.all():
            events_by_country[country.iso3].append(event)

    through = LoadItem.related_go_events.through
    rows = []

    for item in items:
        candidate_events = set()

        for iso3 in item.country_codes:
            for event in events_by_country.get(iso3, []):
                if event.max_affected >= item.total_people_exposed:
                    candidate_events.add(event.id)

        for event_id in candidate_events:
            rows.append(
                through(
                    loaditem_id=item.id,
                    event_id=event_id,
                )
            )
    if rows:
        through.objects.bulk_create(rows, ignore_conflicts=True)


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
