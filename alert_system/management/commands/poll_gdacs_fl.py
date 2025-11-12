from sentry_sdk.crons import monitor

from main.sentry import SentryMonitor

from .poll_base import BasePollingCommand


class Command(BasePollingCommand):
    help = "Poll data for gdacs flood"
    SOURCE_TYPE = "GDACS_FLOOD"

    @monitor(monitor_slug=SentryMonitor.POLL_GDACS_FL)
    def handle(self, *args, **options):
        super().handle(*args, **options)
