from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from sentry_sdk.crons import monitor

from dref.models import (
    DREF_FINAL_REPORT_RECURRING_OVERDUE_INTERVAL_DAYS,
    DREF_FINAL_REPORT_REMINDER_DAYS_BEFORE_DUE,
    Dref,
)
from dref.tasks import (
    send_final_report_implementation_end_email,
    send_final_report_overdue_email,
    send_final_report_recurring_overdue_email,
    send_final_report_reminder_email,
)
from main.sentry import SentryMonitor

# Response (incl. Assessment) and Imminent DREFs only; Loan is out of scope.
IN_SCOPE_DREF_TYPES = [Dref.DrefType.IMMINENT, Dref.DrefType.ASSESSMENT, Dref.DrefType.RESPONSE]

# Final Report is considered submitted once it has been approved (see DrefFinalReportViewSet.get_approved).
NOT_SUBMITTED_FILTER = Q(dreffinalreport__isnull=True) | ~Q(dreffinalreport__status=Dref.Status.APPROVED)


class Command(BaseCommand):
    help = "Send DREF Final Report alert emails (implementation end, reminder, overdue, recurring overdue)."

    @monitor(monitor_slug=SentryMonitor.DREF_FINAL_REPORT_ALERT)
    def handle(self, *args, **options):
        today = timezone.now().date()

        self.send_implementation_end_alerts(today)
        self.send_reminder_alerts(today)
        self.send_overdue_alerts(today)
        self.send_recurring_overdue_alerts(today)

    def send_implementation_end_alerts(self, today):
        queryset = Dref.objects.filter(
            type_of_dref__in=IN_SCOPE_DREF_TYPES,
            end_date=today,
            final_report_implementation_end_alert_sent_at__isnull=True,
        ).filter(NOT_SUBMITTED_FILTER)

        for instance in queryset.iterator():
            self.stdout.write(self.style.NOTICE(f"Sending implementation end alert for Dref ID={instance.id}"))
            send_final_report_implementation_end_email(instance.id)

    def send_reminder_alerts(self, today):
        target_due_date = today + timedelta(days=DREF_FINAL_REPORT_REMINDER_DAYS_BEFORE_DUE)
        queryset = Dref.objects.filter(
            type_of_dref__in=IN_SCOPE_DREF_TYPES,
            final_report_due_date=target_due_date,
            final_report_reminder_alert_sent_at__isnull=True,
        ).filter(NOT_SUBMITTED_FILTER)

        for instance in queryset.iterator():
            self.stdout.write(self.style.NOTICE(f"Sending final report reminder for Dref ID={instance.id}"))
            send_final_report_reminder_email(instance.id)

    def send_overdue_alerts(self, today):
        queryset = Dref.objects.filter(
            type_of_dref__in=IN_SCOPE_DREF_TYPES,
            final_report_due_date=today,
            final_report_overdue_alert_sent_at__isnull=True,
        ).filter(NOT_SUBMITTED_FILTER)

        for instance in queryset.iterator():
            self.stdout.write(self.style.NOTICE(f"Sending final report overdue alert for Dref ID={instance.id}"))
            send_final_report_overdue_email(instance.id)

    def send_recurring_overdue_alerts(self, today):
        recur_before = today - timedelta(days=DREF_FINAL_REPORT_RECURRING_OVERDUE_INTERVAL_DAYS)
        queryset = Dref.objects.filter(
            type_of_dref__in=IN_SCOPE_DREF_TYPES,
            final_report_overdue_alert_sent_at__isnull=False,
            final_report_recurring_overdue_alert_sent_at__date__lte=recur_before,
        ).filter(NOT_SUBMITTED_FILTER)

        for instance in queryset.iterator():
            self.stdout.write(self.style.NOTICE(f"Sending recurring overdue alert for Dref ID={instance.id}"))
            send_final_report_recurring_overdue_email(instance.id)
