import logging

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.db import transaction
from django.utils import timezone

from .extraction import BaseExtractionClass
from .models import Connector

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, retry_backoff=True)
def process_connector_task(self, connector_id):
    """
    Celery task to run ETL for one connector.
    """
    connector = Connector.objects.get(id=connector_id)
    connector.status = Connector.Status.RUNNING
    connector.save(update_fields=["status"])

    connector_label = connector.ConnectorType(connector.type).label

    try:
        logger.info(f"[ETL] Starting connector: {connector_label}")

        # Run ETL inside a transaction
        with transaction.atomic():
            processor = BaseExtractionClass(connector)
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
