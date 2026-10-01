from datetime import timedelta
from unittest import mock

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from dref.factories.dref import DrefFactory, DrefFinalReportFactory
from dref.models import (
    DREF_FINAL_REPORT_DUE_DAYS,
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


class DrefFinalReportDueDateTest(TestCase):
    def test_due_date_computed_on_save(self):
        today = timezone.now().date()
        dref = DrefFactory.create(end_date=today)
        self.assertEqual(dref.final_report_due_date, today + timedelta(days=DREF_FINAL_REPORT_DUE_DAYS))

    def test_due_date_is_none_without_end_date(self):
        dref = DrefFactory.create(end_date=None)
        self.assertIsNone(dref.final_report_due_date)

    def test_due_date_recomputed_when_end_date_changes(self):
        today = timezone.now().date()
        dref = DrefFactory.create(end_date=today)
        dref.end_date = today + timedelta(days=10)
        dref.save()
        self.assertEqual(dref.final_report_due_date, today + timedelta(days=10 + DREF_FINAL_REPORT_DUE_DAYS))


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

    @mock.patch("dref.tasks.send_notification")
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

    @mock.patch("dref.tasks.send_notification")
    def test_send_final_report_reminder_email(self, mock_send_notification):
        send_final_report_reminder_email(self.dref.id)

        mock_send_notification.assert_called_once()
        self.dref.refresh_from_db()
        self.assertIsNotNone(self.dref.final_report_reminder_alert_sent_at)

    @mock.patch("dref.tasks.send_notification")
    def test_send_final_report_overdue_email_seeds_recurring_timestamp(self, mock_send_notification):
        send_final_report_overdue_email(self.dref.id)

        mock_send_notification.assert_called_once()
        self.dref.refresh_from_db()
        self.assertIsNotNone(self.dref.final_report_overdue_alert_sent_at)
        self.assertIsNotNone(self.dref.final_report_recurring_overdue_alert_sent_at)

    @mock.patch("dref.tasks.send_notification")
    def test_send_final_report_recurring_overdue_email(self, mock_send_notification):
        send_final_report_recurring_overdue_email(self.dref.id)

        mock_send_notification.assert_called_once()
        self.dref.refresh_from_db()
        self.assertIsNotNone(self.dref.final_report_recurring_overdue_alert_sent_at)

    @mock.patch("dref.tasks.send_notification")
    def test_task_is_noop_for_missing_dref(self, mock_send_notification):
        result = send_final_report_reminder_email(999999)

        self.assertIsNone(result)
        mock_send_notification.assert_not_called()


@mock.patch("dref.management.commands.dref_final_report_alert.send_final_report_recurring_overdue_email")
@mock.patch("dref.management.commands.dref_final_report_alert.send_final_report_overdue_email")
@mock.patch("dref.management.commands.dref_final_report_alert.send_final_report_reminder_email")
@mock.patch("dref.management.commands.dref_final_report_alert.send_final_report_implementation_end_email")
class DrefFinalReportAlertCommandTest(TestCase):
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

    def test_reminder_alert_sent_30_days_before_due_date(
        self, mock_implementation_end, mock_reminder, mock_overdue, mock_recurring
    ):
        end_date = self.today - timedelta(days=DREF_FINAL_REPORT_DUE_DAYS - DREF_FINAL_REPORT_REMINDER_DAYS_BEFORE_DUE)
        dref = self._create_dref(end_date=end_date)

        call_command("dref_final_report_alert")

        mock_reminder.assert_called_once_with(dref.id)

    def test_overdue_alert_sent_when_due_date_is_today(
        self, mock_implementation_end, mock_reminder, mock_overdue, mock_recurring
    ):
        end_date = self.today - timedelta(days=DREF_FINAL_REPORT_DUE_DAYS)
        dref = self._create_dref(end_date=end_date)

        call_command("dref_final_report_alert")

        mock_overdue.assert_called_once_with(dref.id)

    def test_recurring_overdue_alert_sent_after_interval_elapsed(
        self, mock_implementation_end, mock_reminder, mock_overdue, mock_recurring
    ):
        last_sent = timezone.now() - timedelta(days=DREF_FINAL_REPORT_RECURRING_OVERDUE_INTERVAL_DAYS)
        dref = self._create_dref(
            end_date=self.today - timedelta(days=200),
            final_report_overdue_alert_sent_at=last_sent,
            final_report_recurring_overdue_alert_sent_at=last_sent,
        )

        call_command("dref_final_report_alert")

        mock_recurring.assert_called_once_with(dref.id)

    def test_recurring_overdue_alert_skipped_before_interval_elapses(
        self, mock_implementation_end, mock_reminder, mock_overdue, mock_recurring
    ):
        last_sent = timezone.now() - timedelta(days=DREF_FINAL_REPORT_RECURRING_OVERDUE_INTERVAL_DAYS - 1)
        self._create_dref(
            end_date=self.today - timedelta(days=200),
            final_report_overdue_alert_sent_at=last_sent,
            final_report_recurring_overdue_alert_sent_at=last_sent,
        )

        call_command("dref_final_report_alert")

        mock_recurring.assert_not_called()

    def test_recurring_overdue_alert_skipped_when_final_report_approved(
        self, mock_implementation_end, mock_reminder, mock_overdue, mock_recurring
    ):
        last_sent = timezone.now() - timedelta(days=DREF_FINAL_REPORT_RECURRING_OVERDUE_INTERVAL_DAYS)
        dref = self._create_dref(
            end_date=self.today - timedelta(days=200),
            final_report_overdue_alert_sent_at=last_sent,
            final_report_recurring_overdue_alert_sent_at=last_sent,
        )
        DrefFinalReportFactory.create(dref=dref, status=Dref.Status.APPROVED)

        call_command("dref_final_report_alert")

        mock_recurring.assert_not_called()
