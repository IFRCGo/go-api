from django.core.management.base import BaseCommand

from main.sentry import SentryMonitor


class Command(BaseCommand):

    help = "Validate SentryMonitor cron jobs with Helm values.yaml"

    def handle(self, *args, **options):
        SentryMonitor.validate_config()
        self.stdout.write(self.style.SUCCESS("SentryMonitor is in sync with values.yaml"))
