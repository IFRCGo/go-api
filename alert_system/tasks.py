import logging

from celery import shared_task

from .extraction import process_connector
from .models import Connector

logger = logging.getLogger(__name__)


@shared_task
def process_connector_task(connector_id):
    """
    Celery task to run ETL for one connector.
    """
    connector = Connector.objects.get(id=connector_id)
    try:
        logger.info(f"[ETL] Starting connector: {connector.type}")
        process_connector(connector)
        logger.info(f"[ETL] Completed connector: {connector.type}")
    except Exception as e:
        logger.exception(f"[ETL] Connector {connector.id} failed: {e}")
        raise e
