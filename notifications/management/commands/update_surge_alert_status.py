import logging
from sentry_sdk.crons import monitor

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import models

from notifications.models import SurgeAlert, SurgeAlertStatus
from api.models import CronJob, CronJobStatus
from main.sentry import SentryMonitor


logger = logging.getLogger(__name__)


@monitor(monitor_slug=SentryMonitor.UPDATE_SURGE_ALERT_STATUS)
class Command(BaseCommand):
    '''
        Updating the Surge Alert Status according:
        If the alert status is marked as stood_down, then the status is Stood Down.
        If the closing timestamp (closes) is earlier than the current date, the status is displayed as Closed.
        Otherwise, it is displayed as Open.
    '''
    help = 'Update surge alert status'

    def handle(self, *args, **options):
        now = timezone.now()
        try:
            logger.info('Updating Surge alerts status')
            SurgeAlert.objects.update(
                status=models.Case(
                    models.When(is_stood_down=True, then=models.Value(SurgeAlertStatus.STOOD_DOWN)),
                    models.When(closes__lt=now, then=models.Value(SurgeAlertStatus.CLOSED)),
                    models.When(closes__gte=now, then=models.Value(SurgeAlertStatus.OPEN)),
                    default=models.F('status'),
                    output_field=models.IntegerField()
                )
            )
            CronJob.sync_cron({
                'name': 'update_surge_alert_status',
                'message': 'Updated Surge alerts status',
                'status': CronJobStatus.SUCCESSFUL,
            })
            logger.info('Updated Surge alerts status')
        except Exception as e:
            CronJob.sync_cron({
                'name': 'update_surge_alert_status',
                'message': f'Error while updating Surge alerts status\n\nException:\n{str(e)}',
                'status': CronJobStatus.ERRONEOUS,
            })
            logger.error('Error while updating surge alerts status', exc_info=True)
