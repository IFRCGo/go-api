from poll_base import BasePollingCommand
from sentry_sdk.crons import monitor

from main.sentry import SentryMonitor


class Command(BasePollingCommand):
    help = "Poll data for gdacs cyclone"
    SOURCE_TYPE = "GDACS_CYCLONE"

    @monitor(monitor_slug=SentryMonitor.POLL_GDACS_CY)
    def handle(self, *args, **options):
        super().handle(*args, **options)
