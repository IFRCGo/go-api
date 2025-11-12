from sentry_sdk.crons import monitor

from main.sentry import SentryMonitor

from .poll_base import BasePollingCommand


class Command(BasePollingCommand):
    help = "Poll data for usgs eartquake"
    SOURCE_TYPE = "USGS_EARTHQUAKE"

    @monitor(monitor_slug=SentryMonitor.POLL_USGS_EQ)
    def handle(self, *args, **options):
        super().handle(*args, **options)
