from django.core.management.base import BaseCommand
from sentry_sdk import monitor

from alert_system.email_processing import process_email_alert
from alert_system.models import LoadItem
from main.sentry import SentryMonitor

# NOTE: Disabled parallel processing to avoid inconsistent state and keep
#  execution deterministic. Email logic is intentionally moved out of tasks.py for now.
#  If reintroduced later, a Celery chain may be used to ensure proper ordering
#  and retry management.


class Command(BaseCommand):
    help = "Send alert email notifications for eligible load items"

    @monitor(monitor_slug=SentryMonitor.ALERT_NOTIFICATION)
    def handle(self, *args, **options):

        items = LoadItem.objects.filter(item_eligible=True, is_past_event=False)

        if not items.exists():
            self.stdout.write(self.style.NOTICE("No eligible items found"))
            return

        self.stdout.write(self.style.NOTICE(f"Processing {items.count()} items for alert email notification."))

        for item in items.iterator():
            process_email_alert(load_item_id=item.id)
        self.stdout.write(self.style.SUCCESS("All alert notification emails processed successfully"))
