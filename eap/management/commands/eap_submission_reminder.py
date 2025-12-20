from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from sentry_sdk.crons import monitor

from eap.models import EAPRegistration
from eap.tasks import send_deadline_reminder_email
from main.sentry import SentryMonitor


class Command(BaseCommand):
    help = "Send EAP submission reminder emails 10 days before deadline"

    @monitor(monitor_slug=SentryMonitor.EAP_SUBMISSION_REMINDER)
    def handle(self, *args, **options):
        """
        Finds EAP-registrations whose submission deadline is exactly 10 days from today
        and sends reminder emails for each matching registration.
        """
        target_date = timezone.now().date() + timedelta(days=10)
        queryset = EAPRegistration.objects.filter(
            dead_line=target_date,
        )

        if not queryset.exists():
            self.stdout.write(self.style.NOTICE("No EAP registrations found for deadline reminder."))
            return

        for instance in queryset:
            self.stdout.write(self.style.NOTICE(f"Sending deadline reminder email for EAPRegistration ID={instance.id}"))
            send_deadline_reminder_email(instance.id)

        self.stdout.write(self.style.SUCCESS("Successfully sent all deadline reminder emails."))
