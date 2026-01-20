import logging

from django.core.management.base import BaseCommand

from alert_system.models import Connector
from alert_system.tasks import process_connector_task

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Command to extract data of gdacs-flood from eoapi"

    SOURCE_TYPE = Connector.ConnectorType.GDACS_FLOOD

    def handle(self, *args, **options):
        connector = Connector.objects.filter(type=self.SOURCE_TYPE).first()
        if not connector:
            logger.warning("No connectors found.")
            return

        self.stdout.write(f"Starting extraction task for {connector}")

        process_connector_task.delay(connector.id)

        logger.info("Connector task dispatched.")
