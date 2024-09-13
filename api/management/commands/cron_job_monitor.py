import logging
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from main.sentry import SentryMonitor, SentryMonitorConfig
from main.settings import SENTRY_DSN

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    help = "This command is used to create a cron job monitor for sentry"

    def add_arguments(self, parser):
        parser.add_argument(
            "--validate-only",
            dest="validate_only",
            action="store_true",
        )

    def handle(self, *args, **options):
        SentryMonitor.validate_config()

        if not SENTRY_DSN:
            logger.error("SENTRY_DSN is not set in the environment variables. Exiting...")
            return

        if options.get("validate_only"):
            return

        parsed_url = urlparse(SENTRY_DSN)
        project_id = parsed_url.path.strip("/")
        api_key = parsed_url.username

        SENTRY_INGEST = f"https://{parsed_url.hostname}"

        for cronjob in SentryMonitor.choices:
            job, schedule = cronjob
            SENTRY_CRONS = f"{SENTRY_INGEST}/api/{project_id}/cron/{job}/{api_key}/"

            payload = {
                "monitor_config": {
                    "schedule": {
                        "type": "crontab",
                        "value": str(schedule),
                    },
                    "tz": settings.TIME_ZONE,
                    "checkin_margin": SentryMonitorConfig.get_checkin_margin(cronjob),
                    "failure_issue_threshold": SentryMonitorConfig.get_failure_issue_threshold(cronjob),
                    "recovery_threshold": SentryMonitorConfig.get_recovery_threshold(cronjob),
                },
                "environment": settings.GO_ENVIRONMENT,
                "status": "ok",
            }

            response = requests.post(SENTRY_CRONS, json=payload, headers={"Content-Type": "application/json"})
            if response.status_code == 202:
                self.stdout.write(self.style.SUCCESS(f"Successfully created cron job for {job}"))
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to create cron job for {job} with status code {response.status_code}: {response.content}"
                    )
                )
