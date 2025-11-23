import logging

from django.core.management.base import BaseCommand

from alert_system.models import Connector
from alert_system.tasks import process_connector_task

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Command to extract data of gdacs-flood from eoapi"

    SOURCE_TYPE = 100

    def handle(self, *args, **options):
        if not self.SOURCE_TYPE:
            raise ValueError("SOURCE_TYPE must be defined")
        self.stdout.write("Starting extraction task...")
        connector = Connector.objects.filter(type=self.SOURCE_TYPE).first()
        if not connector:
            logger.warning("No connectors found.")
            return

        process_connector_task.delay(connector.id)

        logger.info("Connector task dispatched.")

        self.stdout.write("Extraction task finished.")
