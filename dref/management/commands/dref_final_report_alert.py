from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from sentry_sdk.crons import monitor

from dref.models import (
    DREF_FINAL_REPORT_DUE_MONTHS,
    DREF_FINAL_REPORT_RECURRING_OVERDUE_INTERVAL_MONTHS,
    DREF_FINAL_REPORT_REMINDER_MONTHS_BEFORE_DUE,
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
        # "1 month before the due date" == "2 months after end_date" (due date itself is end_date + 3
        # months) - computed directly from end_date, not by subtracting a month from final_report_due_date,
        # to avoid relativedelta's day-of-month clamping producing an inconsistent result between the two.
        months_before_end_date = DREF_FINAL_REPORT_DUE_MONTHS - DREF_FINAL_REPORT_REMINDER_MONTHS_BEFORE_DUE
        target_end_date = today - relativedelta(months=months_before_end_date)
        queryset = Dref.objects.filter(
            type_of_dref__in=IN_SCOPE_DREF_TYPES,
            end_date=target_end_date,
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
        # Anchored to final_report_due_date (not chained off the last send) so a due date that falls on
        # a day some later months don't have (e.g. the 31st) still recurs on a consistent, driftless
        # schedule every month. final_report_recurring_overdue_alert_sent_at is only used to skip a
        # same-day re-run of the command.
        queryset = Dref.objects.filter(
            type_of_dref__in=IN_SCOPE_DREF_TYPES,
            final_report_overdue_alert_sent_at__isnull=False,
            final_report_due_date__isnull=False,
            final_report_due_date__lt=today,
        ).filter(NOT_SUBMITTED_FILTER)

        for instance in queryset.iterator():
            if instance.final_report_recurring_overdue_alert_sent_at and (
                instance.final_report_recurring_overdue_alert_sent_at.date() == today
            ):
                continue

            due_date = instance.final_report_due_date
            months_elapsed = (today.year - due_date.year) * 12 + (today.month - due_date.month)
            if months_elapsed < DREF_FINAL_REPORT_RECURRING_OVERDUE_INTERVAL_MONTHS:
                continue
            if due_date + relativedelta(months=months_elapsed) != today:
                continue

            self.stdout.write(self.style.NOTICE(f"Sending recurring overdue alert for Dref ID={instance.id}"))
            send_final_report_recurring_overdue_email(instance.id)
