from datetime import timedelta
from unittest import mock

from dateutil.relativedelta import relativedelta
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from dref.factories.dref import DrefFactory, DrefFinalReportFactory
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


class DrefFinalReportDueDateTest(TestCase):
    def test_due_date_computed_on_save(self):
        today = timezone.now().date()
        dref = DrefFactory.create(end_date=today)
        self.assertEqual(dref.final_report_due_date, today + relativedelta(months=DREF_FINAL_REPORT_DUE_MONTHS))

    def test_due_date_is_none_without_end_date(self):
        dref = DrefFactory.create(end_date=None)
        self.assertIsNone(dref.final_report_due_date)

    def test_due_date_recomputed_when_end_date_changes(self):
        today = timezone.now().date()
        dref = DrefFactory.create(end_date=today)
        dref.end_date = today + timedelta(days=10)
        dref.save()
        self.assertEqual(
            dref.final_report_due_date, today + timedelta(days=10) + relativedelta(months=DREF_FINAL_REPORT_DUE_MONTHS)
        )


class DrefFinalReportAlertTasksTest(TestCase):
    def setUp(self):
        self.dref = DrefFactory.create(
            appeal_code="MDRXX001",
            end_date=timezone.now().date(),
            ifrc_appeal_manager_email="appeal.manager@example.com",
            ifrc_project_manager_email="project.manager@example.com",
            national_society_contact_email="ns.contact@example.com",
            regional_focal_point_email="regional.focal@example.com",
        )

    @mock.patch("dref.tasks.send_notification_dref")
    def test_send_final_report_implementation_end_email(self, mock_send_notification):
        send_final_report_implementation_end_email(self.dref.id)

        mock_send_notification.assert_called_once()
        _, kwargs = mock_send_notification.call_args
        self.assertIn("appeal.manager@example.com", kwargs["recipients"])
        self.assertIn("project.manager@example.com", kwargs["recipients"])
        self.assertIn("ns.contact@example.com", kwargs["recipients"])
        self.assertIn("regional.focal@example.com", kwargs["cc_recipients"])
        self.assertIn("MDRXX001", kwargs["subject"])

        self.dref.refresh_from_db()
        self.assertIsNotNone(self.dref.final_report_implementation_end_alert_sent_at)

    @mock.patch("dref.tasks.send_notification_dref")
    def test_send_final_report_reminder_email(self, mock_send_notification):
        send_final_report_reminder_email(self.dref.id)

        mock_send_notification.assert_called_once()
        self.dref.refresh_from_db()
        self.assertIsNotNone(self.dref.final_report_reminder_alert_sent_at)

    @mock.patch("dref.tasks.send_notification_dref")
    def test_send_final_report_overdue_email_seeds_recurring_timestamp(self, mock_send_notification):
        send_final_report_overdue_email(self.dref.id)

        mock_send_notification.assert_called_once()
        self.dref.refresh_from_db()
        self.assertIsNotNone(self.dref.final_report_overdue_alert_sent_at)
        self.assertIsNotNone(self.dref.final_report_recurring_overdue_alert_sent_at)

    @mock.patch("dref.tasks.send_notification_dref")
    def test_send_final_report_recurring_overdue_email(self, mock_send_notification):
        send_final_report_recurring_overdue_email(self.dref.id)

        mock_send_notification.assert_called_once()
        self.dref.refresh_from_db()
        self.assertIsNotNone(self.dref.final_report_recurring_overdue_alert_sent_at)

    @mock.patch("dref.tasks.send_notification_dref")
    def test_task_is_noop_for_missing_dref(self, mock_send_notification):
        result = send_final_report_reminder_email(999999)

        self.assertIsNone(result)
        mock_send_notification.assert_not_called()


@mock.patch("dref.management.commands.dref_final_report_alert.send_final_report_recurring_overdue_email")
@mock.patch("dref.management.commands.dref_final_report_alert.send_final_report_overdue_email")
@mock.patch("dref.management.commands.dref_final_report_alert.send_final_report_reminder_email")
@mock.patch("dref.management.commands.dref_final_report_alert.send_final_report_implementation_end_email")
class DrefFinalReportAlertCommandTest(TestCase):
    # end_date this far in the past puts final_report_due_date exactly 1 recurring interval ago.
    RECURRING_DUE_MONTHS_AGO = DREF_FINAL_REPORT_DUE_MONTHS + DREF_FINAL_REPORT_RECURRING_OVERDUE_INTERVAL_MONTHS

    def setUp(self):
        self.today = timezone.now().date()

    def _create_dref(self, **kwargs):
        kwargs.setdefault("type_of_dref", Dref.DrefType.RESPONSE)
        return DrefFactory.create(**kwargs)

    def test_implementation_end_alert_sent_when_end_date_is_today(
        self, mock_implementation_end, mock_reminder, mock_overdue, mock_recurring
    ):
        dref = self._create_dref(end_date=self.today)

        call_command("dref_final_report_alert")

        mock_implementation_end.assert_called_once_with(dref.id)

    def test_implementation_end_alert_skipped_for_loan_type(
        self, mock_implementation_end, mock_reminder, mock_overdue, mock_recurring
    ):
        self._create_dref(end_date=self.today, type_of_dref=Dref.DrefType.LOAN)

        call_command("dref_final_report_alert")

        mock_implementation_end.assert_not_called()

    def test_implementation_end_alert_skipped_once_already_sent(
        self, mock_implementation_end, mock_reminder, mock_overdue, mock_recurring
    ):
        self._create_dref(end_date=self.today, final_report_implementation_end_alert_sent_at=timezone.now())

        call_command("dref_final_report_alert")

        mock_implementation_end.assert_not_called()

    def test_implementation_end_alert_skipped_when_final_report_approved(
        self, mock_implementation_end, mock_reminder, mock_overdue, mock_recurring
    ):
        dref = self._create_dref(end_date=self.today)
        DrefFinalReportFactory.create(dref=dref, status=Dref.Status.APPROVED)

        call_command("dref_final_report_alert")

        mock_implementation_end.assert_not_called()

    def test_implementation_end_alert_not_skipped_for_draft_final_report(
        self, mock_implementation_end, mock_reminder, mock_overdue, mock_recurring
    ):
        dref = self._create_dref(end_date=self.today)
        DrefFinalReportFactory.create(dref=dref, status=Dref.Status.DRAFT)

        call_command("dref_final_report_alert")

        mock_implementation_end.assert_called_once_with(dref.id)

    def test_reminder_alert_sent_1_month_before_due_date(
        self, mock_implementation_end, mock_reminder, mock_overdue, mock_recurring
    ):
        end_date = self.today - relativedelta(months=DREF_FINAL_REPORT_DUE_MONTHS - DREF_FINAL_REPORT_REMINDER_MONTHS_BEFORE_DUE)
        dref = self._create_dref(end_date=end_date)

        call_command("dref_final_report_alert")

        mock_reminder.assert_called_once_with(dref.id)

    def test_overdue_alert_sent_when_due_date_is_today(
        self, mock_implementation_end, mock_reminder, mock_overdue, mock_recurring
    ):
        end_date = self.today - relativedelta(months=DREF_FINAL_REPORT_DUE_MONTHS)
        dref = self._create_dref(end_date=end_date)

        call_command("dref_final_report_alert")

        mock_overdue.assert_called_once_with(dref.id)

    def test_implementation_end_alert_catches_up_when_end_date_is_in_the_past(
        self, mock_implementation_end, mock_reminder, mock_overdue, mock_recurring
    ):
        # Simulates a Dref whose implementation end date was missed (e.g. cron downtime) and never
        # triggered an alert - the catch-up filter (end_date <= today) must still send it.
        end_date = self.today - timedelta(days=5)
        dref = self._create_dref(end_date=end_date)

        call_command("dref_final_report_alert")

        mock_implementation_end.assert_called_once_with(dref.id)

    def test_reminder_alert_catches_up_when_reminder_date_is_in_the_past(
        self, mock_implementation_end, mock_reminder, mock_overdue, mock_recurring
    ):
        # Simulates a Dref whose reminder date was missed and never triggered an alert - the catch-up
        # filter (end_date <= target_end_date) must still send it.
        end_date = (
            self.today
            - relativedelta(months=DREF_FINAL_REPORT_DUE_MONTHS - DREF_FINAL_REPORT_REMINDER_MONTHS_BEFORE_DUE)
            - timedelta(days=5)
        )
        dref = self._create_dref(end_date=end_date)

        call_command("dref_final_report_alert")

        mock_reminder.assert_called_once_with(dref.id)

    def test_overdue_alert_catches_up_when_due_date_is_in_the_past_and_never_sent(
        self, mock_implementation_end, mock_reminder, mock_overdue, mock_recurring
    ):
        # Regression test for the "stuck record" bug: a Dref whose final_report_due_date already passed,
        # but which never received an overdue alert (e.g. because it missed the previous exact-day
        # match), must be caught up by the next run instead of being permanently skipped - which also
        # unblocks recurring overdue alerts from ever starting for it.
        end_date = self.today - relativedelta(months=DREF_FINAL_REPORT_DUE_MONTHS) - timedelta(days=60)
        dref = self._create_dref(end_date=end_date)

        call_command("dref_final_report_alert")

        mock_overdue.assert_called_once_with(dref.id)

    def test_recurring_overdue_alert_sent_after_interval_elapsed(
        self, mock_implementation_end, mock_reminder, mock_overdue, mock_recurring
    ):
        # end_date + 4 months = due_date (end_date + 3 months) + 1 recurring interval = today.
        last_sent = timezone.now() - timedelta(days=35)
        dref = self._create_dref(
            end_date=self.today - relativedelta(months=self.RECURRING_DUE_MONTHS_AGO),
            final_report_overdue_alert_sent_at=last_sent,
            final_report_recurring_overdue_alert_sent_at=last_sent,
        )

        call_command("dref_final_report_alert")

        mock_recurring.assert_called_once_with(dref.id)

    def test_recurring_overdue_alert_skipped_before_interval_elapses(
        self, mock_implementation_end, mock_reminder, mock_overdue, mock_recurring
    ):
        # due_date lands ~10 days ago - overdue, but less than a full recurring interval has elapsed.
        end_date = (self.today - timedelta(days=10)) - relativedelta(months=DREF_FINAL_REPORT_DUE_MONTHS)
        last_sent = timezone.now() - timedelta(days=10)
        self._create_dref(
            end_date=end_date,
            final_report_overdue_alert_sent_at=last_sent,
            final_report_recurring_overdue_alert_sent_at=last_sent,
        )

        call_command("dref_final_report_alert")

        mock_recurring.assert_not_called()

    def test_recurring_overdue_alert_skipped_if_already_sent_today(
        self, mock_implementation_end, mock_reminder, mock_overdue, mock_recurring
    ):
        last_sent = timezone.now()
        self._create_dref(
            end_date=self.today - relativedelta(months=self.RECURRING_DUE_MONTHS_AGO),
            final_report_overdue_alert_sent_at=last_sent - timedelta(days=35),
            final_report_recurring_overdue_alert_sent_at=last_sent,
        )

        call_command("dref_final_report_alert")

        mock_recurring.assert_not_called()

    def test_recurring_overdue_alert_skipped_when_final_report_approved(
        self, mock_implementation_end, mock_reminder, mock_overdue, mock_recurring
    ):
        last_sent = timezone.now() - timedelta(days=35)
        dref = self._create_dref(
            end_date=self.today - relativedelta(months=self.RECURRING_DUE_MONTHS_AGO),
            final_report_overdue_alert_sent_at=last_sent,
            final_report_recurring_overdue_alert_sent_at=last_sent,
        )
        DrefFinalReportFactory.create(dref=dref, status=Dref.Status.APPROVED)

        call_command("dref_final_report_alert")

        mock_recurring.assert_not_called()
