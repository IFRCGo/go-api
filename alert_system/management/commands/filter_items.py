import logging

from django.core.management.base import BaseCommand

from alert_system.tasks import validate_all_connectors

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Command to filter all data from the StacItems table"

    def handle(self, *args, **options):
        self.stdout.write("Starting filtration task...")

        validate_all_connectors.delay()

        logger.info("Connector filtration task dispatched for all connectors")

        self.stdout.write("Filtration task finished.")
