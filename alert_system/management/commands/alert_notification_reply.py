from django.core.management.base import BaseCommand

from alert_system.models import AlertEmailLog, LoadItem
from alert_system.tasks import send_alert_email_replies

# TODO @sudip-khanal:Configure Sentry monitoring and values.yaml entry once the execution time is confirmed.


class Command(BaseCommand):
    help = "Send reply emails for new items sharing same correlation id with already sent root emails"

    def handle(self, *args, **options):

        # correlation IDs of already sent emails
        correlation_ids = (
            AlertEmailLog.objects.filter(
                status=AlertEmailLog.Status.SENT,
            )
            .values_list("item__correlation_id", flat=True)
            .distinct()
        )

        if not correlation_ids:
            self.stdout.write(self.style.NOTICE("No sent emails found for reply to."))
            return

        # New items that belong to same correlation IDs but have Not been emailed yet
        items = LoadItem.objects.filter(correlation_id__in=correlation_ids, item_eligible=True, is_past_event=False).exclude(
            email_alert_load_item__status=AlertEmailLog.Status.SENT
        )

        if not items.exists():
            self.stdout.write(self.style.NOTICE("No new related items found for replies."))
            return

        self.stdout.write(self.style.NOTICE(f"Queueing {items.count()} reply emails."))

        # Step 3: Queue reply emails
        for item in items.iterator():
            send_alert_email_replies.delay(load_item_id=item.id)

        self.stdout.write(self.style.SUCCESS("All reply emails have been queued successfully."))
