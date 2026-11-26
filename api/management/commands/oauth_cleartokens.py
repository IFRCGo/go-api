from django.core import management
from django.core.management.base import BaseCommand

from main.sentry import SentryMonitor, sentry_cron_monitor


class Command(BaseCommand):
    help = "A wrapper for cleartokens command to track using sentry cron monitor. Feel free to use cleartokens"

    @sentry_cron_monitor(SentryMonitor.OAUTH_CLEARTOKENS)
    def handle(self, *args, **kwargs):
        management.call_command("cleartokens")
