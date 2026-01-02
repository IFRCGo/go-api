from django.core.management.base import BaseCommand
from sentry_sdk import monitor

from alert_system.models import LoadItem
from alert_system.tasks import send_alert_email_notification
from main.sentry import SentryMonitor


class Command(BaseCommand):
    help = "Send daily alert email notifications for eligible load items"

    @monitor(monitor_slug=SentryMonitor.ALERT_NOTIFICATION)
    def handle(self, *args, **options):

        items = LoadItem.objects.filter(item_eligible=True, is_past_event=False)

        if not items.exists():
            self.stdout.write(self.style.WARNING("No eligible items found"))
            return

        self.stdout.write(self.style.NOTICE("Sending alert email notification"))

        for item in items:
            send_alert_email_notification.delay(load_item_id=item.id)

        self.stdout.write(self.style.SUCCESS("All alert notification email send successfully"))
