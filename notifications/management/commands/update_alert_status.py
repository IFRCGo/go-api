import logging
from django.db import models

from django.core.management.base import BaseCommand
from django.utils import timezone
from notifications.models import SurgeAlert, SurgeAlertStatus

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    '''
        Updating the Alert Status according:
        If the alert status is marked as stood_down, then the status is Stood Down.
        If the closing timestamp (closes) is earlier than the current date, the status is displayed as Closed. Otherwise, it is displayed as Open.
    '''
    help = 'Update alert status'

    def handle(self, *args, **options):
        now = timezone.now()
        try:
            SurgeAlert.objects.exclude(status=SurgeAlertStatus.CLOSED).filter(
                models.Q(opens__lte=now, closes__gte=now) | models.Q(is_stood_down=True)
            ).update(
                status=models.Case(
                    models.When(opens__lte=now, closes__gte=now, then=models.Value(SurgeAlertStatus.OPEN)),
                    models.When(closes__lt=now, then=models.Value(SurgeAlertStatus.CLOSED)),
                    models.When(is_stood_down=True, then=models.Value(SurgeAlertStatus.STOOD_DOWN)),
                    default=models.F('status'),
                    output_field=models.IntegerField()
                )
            )
        except Exception as e:
            logger.error('Error while updating alerts status: %s' % str(e))
