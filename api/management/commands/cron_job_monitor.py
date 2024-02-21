import requests
import logging

from urllib.parse import urlparse
from django.core.management.base import BaseCommand
from main.sentry import CRON_JOBS_MONITOR_SCHEDULE

from main.settings import SENTRY_DSN

logger = logging.getLogger(__name__)

class Command(BaseCommand):

    help = "This command is used to create a cron job monitor for sentry"

    def handle(self, *args, **options):
        if not SENTRY_DSN:
            logger.error("SENTRY_DSN is not set in the environment variables. Exiting...")
            return
        parsed_url = urlparse(SENTRY_DSN)
        project_id = parsed_url.path.strip("/")
        api_key = parsed_url.username

        SENTRY_INGEST = f"https://{parsed_url.hostname}"

        for job, schedule in CRON_JOBS_MONITOR_SCHEDULE:
            SENTRY_CRONS = f"{SENTRY_INGEST}/api/{project_id}/cron/{job}/{api_key}/"

            payload = {
                "monitor_config": {
                    "schedule": {
                        "type": "crontab",
                        "value": schedule
                    }
                },
                'environment':'development',
                "status": "ok",
            }

            response = requests.post(SENTRY_CRONS, json=payload, headers={"Content-Type": "application/json"})
            if response.status_code == 202:
                logger.info(f"Successfully created cron job for {job}")
            else:
                logger.error(f"Failed to create cron job for {job} with status code {response.status_code}")
