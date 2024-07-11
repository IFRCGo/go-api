import logging

from django.core.management.base import BaseCommand
from django.db import models
from sentry_sdk.crons import monitor

from api.models import CronJob, CronJobStatus
from main.sentry import SentryMonitor
from notifications.models import SurgeAlert, SurgeAlertStatus

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Updating the Surge Alert Status according:
    If molnix_status is active, status should Open,
    If molnix_status is archived, status should be  Closed,
    If molnix_status is unfilled, status should be Stood Down,
    """

    help = "Update surge alert status"

    @monitor(monitor_slug=SentryMonitor.UPDATE_SURGE_ALERT_STATUS)
    def handle(self, *args, **options):
        try:
            logger.info("Updating Surge alerts status")
            SurgeAlert.objects.update(
                status=models.Case(
                    models.When(molnix_status="active", then=models.Value(SurgeAlertStatus.OPEN)),
                    models.When(molnix_status="archived", then=models.Value(SurgeAlertStatus.CLOSED)),
                    models.When(molnix_status="unfilled", then=models.Value(SurgeAlertStatus.STOOD_DOWN)),
                    default=models.F("status"),
                    output_field=models.IntegerField(),
                )
            )
            CronJob.sync_cron(
                {
                    "name": "update_surge_alert_status",
                    "message": "Updated Surge alerts status",
                    "status": CronJobStatus.SUCCESSFUL,
                }
            )
            logger.info("Updated Surge alerts status")
        except Exception as e:
            CronJob.sync_cron(
                {
                    "name": "update_surge_alert_status",
                    "message": f"Error while updating Surge alerts status\n\nException:\n{str(e)}",
                    "status": CronJobStatus.ERRONEOUS,
                }
            )
            logger.error("Error while updating surge alerts status", exc_info=True)
