from django.core import management
from django.core.management.base import BaseCommand
from sentry_sdk.crons import monitor

from main.sentry import SentryMonitor


class Command(BaseCommand):
    help = "A wrapper for cleartokens command to track using sentry cron monitor. Feel free to use cleartokens"

    @monitor(monitor_slug=SentryMonitor.OAUTH_CLEARTOKENS)
    def handle(self, *args, **kwargs):
        management.call_command("cleartokens")
