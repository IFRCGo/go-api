from datetime import date, timedelta
from importlib import import_module
from unittest import mock

from dateutil.relativedelta import relativedelta
from django.apps import apps
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from dref.factories.dref import (
    DrefFactory,
    DrefFinalReportFactory,
    DrefOperationalUpdateFactory,
)
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
from dref.utils import (
    get_final_report_alert_email_context,
    get_final_report_alert_recipients,
    get_latest_approved_operational_update,
)


class DrefFinalReportDueDateTest(TestCase):
    def setUp(self):
        self.dref = DrefFactory.create(appeal_code="MDRXX001", end_date=date(2026, 1, 31))

    def _create_update(self, **kwargs):
        kwargs.setdefault("dref", self.dref)
        kwargs.setdefault("appeal_code", self.dref.appeal_code)
        kwargs.setdefault("date_of_approval", date(2026, 2, 1))
        kwargs.setdefault("new_operational_end_date", date(2026, 5, 31))
        return DrefOperationalUpdateFactory.create(**kwargs)

    def test_due_date_uses_latest_approved_update_matching_appeal_code(self):
        self._create_update(operational_update_number=1, new_operational_end_date=date(2026, 8, 31))
        self._create_update(
            dref=DrefFactory.create(),
            operational_update_number=2,
            new_operational_end_date=date(2026, 5, 31),
        )
        self._create_update(date_of_approval=None, new_operational_end_date=date(2026, 12, 31))
        self._create_update(appeal_code="MDRXX999", date_of_approval=date(2026, 3, 1))

        self.dref.refresh_from_db()
        self.assertEqual(self.dref.final_report_due_date, date(2026, 8, 31))
        self.dref.save()
        self.dref.refresh_from_db()
        self.assertEqual(self.dref.final_report_due_date, date(2026, 8, 31))
        context = get_final_report_alert_email_context(self.dref)
        self.assertEqual(context["operation_end_date"], date(2026, 5, 31))
        self.assertEqual(context["due_date"], date(2026, 8, 31))

    def test_due_date_falls_back_when_latest_update_has_no_end_date(self):
        self._create_update(operational_update_number=1)
        self._create_update(operational_update_number=2, new_operational_end_date=None)
        self.dref.refresh_from_db()
        self.assertEqual(self.dref.final_report_due_date, date(2026, 4, 30))

    def test_due_date_uses_most_recent_approval_not_largest_end_date_or_update_number(self):
        self._create_update(operational_update_number=10, new_operational_end_date=date(2026, 12, 31))
        self._create_update(
            operational_update_number=1,
            date_of_approval=date(2026, 3, 1),
            new_operational_end_date=date(2026, 4, 30),
        )
        self.dref.refresh_from_db()
        self.assertEqual(self.dref.final_report_due_date, date(2026, 7, 30))

    def test_due_date_uses_update_when_application_has_no_end_date(self):
        self.dref.end_date = None
        self.dref.save()
        self._create_update()
        self.dref.refresh_from_db()
        self.assertEqual(self.dref.final_report_due_date, date(2026, 8, 31))

    def test_due_date_ignores_updates_without_appeal_code(self):
        self.dref.appeal_code = None
        self.dref.save()
        self._create_update(appeal_code=None)
        self.dref.refresh_from_db()
        self.assertEqual(self.dref.final_report_due_date, date(2026, 4, 30))

    def test_due_date_changes_when_update_is_approved_edited_and_deleted(self):
        update = self._create_update(date_of_approval=None)
        self.dref.refresh_from_db()
        self.assertEqual(self.dref.final_report_due_date, date(2026, 4, 30))
        update.date_of_approval = date(2026, 2, 1)
        update.save(update_fields=["date_of_approval"])
        self.dref.refresh_from_db()
        self.assertEqual(self.dref.final_report_due_date, date(2026, 8, 31))
        update.new_operational_end_date = date(2026, 6, 30)
        update.save(update_fields=["new_operational_end_date"])
        self.dref.refresh_from_db()
        self.assertEqual(self.dref.final_report_due_date, date(2026, 9, 30))
        type(update).objects.filter(pk=update.pk).delete()
        self.dref.refresh_from_db()
        self.assertEqual(self.dref.final_report_due_date, date(2026, 4, 30))

    def test_due_date_refreshes_both_appeals_when_update_moves(self):
        other_dref = DrefFactory.create(appeal_code="MDRXX002", end_date=date(2026, 2, 28))
        update = self._create_update()
        update.appeal_code = other_dref.appeal_code
        update.save(update_fields=["appeal_code"])
        self.dref.refresh_from_db()
        other_dref.refresh_from_db()
        self.assertEqual(self.dref.final_report_due_date, date(2026, 4, 30))
        self.assertEqual(other_dref.final_report_due_date, date(2026, 8, 31))

    def test_due_date_persisted_with_partial_application_save(self):
        self.dref.end_date = "2026-02-28"
        self.dref.save(update_fields=["end_date"])
        self.dref.refresh_from_db()
        self.assertEqual(self.dref.final_report_due_date, date(2026, 5, 28))

    def test_partial_save_does_not_use_unsaved_deadline_source_fields(self):
        self._create_update()
        self.dref.end_date = date(2026, 12, 31)
        self.dref.appeal_code = "MDRXX999"
        self.dref.title = "Updated title"
        self.dref.save(update_fields=["title"])
        self.dref.refresh_from_db()
        self.assertEqual(self.dref.final_report_due_date, date(2026, 8, 31))
        self.assertEqual(self.dref.end_date, date(2026, 1, 31))
        self.assertEqual(self.dref.appeal_code, "MDRXX001")

    def test_due_date_falls_back_when_approval_is_removed(self):
        update = self._create_update()
        update.date_of_approval = None
        update.save(update_fields=["date_of_approval"])
        self.dref.refresh_from_db()
        self.assertEqual(self.dref.final_report_due_date, date(2026, 4, 30))

    def test_migration_refreshes_existing_deadlines_without_resetting_alerts(self):
        self._create_update()
        fallback_dref = DrefFactory.create(appeal_code="MDRXX002", end_date=date(2026, 1, 31))
        sent_at = timezone.now()
        Dref.objects.filter(pk__in=[self.dref.pk, fallback_dref.pk]).update(
            final_report_due_date=None,
            final_report_overdue_alert_sent_at=sent_at,
        )
        migration = import_module("dref.migrations.0094_refresh_final_report_due_dates")

        migration.refresh_final_report_due_dates(apps, mock.Mock(connection=mock.Mock(alias="default")))

        self.dref.refresh_from_db()
        fallback_dref.refresh_from_db()
        self.assertEqual(self.dref.final_report_due_date, date(2026, 8, 31))
        self.assertEqual(fallback_dref.final_report_due_date, date(2026, 4, 30))
        self.assertEqual(self.dref.final_report_overdue_alert_sent_at, sent_at)
        self.assertEqual(fallback_dref.final_report_overdue_alert_sent_at, sent_at)

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

    def test_alerts_wait_for_approved_operational_extension(
        self, mock_implementation_end, mock_reminder, mock_overdue, mock_recurring
    ):
        dref = self._create_dref(
            appeal_code="MDRXX001",
            end_date=self.today - relativedelta(months=self.RECURRING_DUE_MONTHS_AGO),
        )
        DrefOperationalUpdateFactory.create(
            dref=dref,
            appeal_code=dref.appeal_code,
            date_of_approval=self.today,
            new_operational_end_date=self.today + relativedelta(months=1),
        )

        call_command("dref_final_report_alert")

        mock_implementation_end.assert_not_called()
        mock_reminder.assert_not_called()
        mock_overdue.assert_not_called()
        mock_recurring.assert_not_called()

    def test_reminder_uses_approved_operational_end_date(
        self, mock_implementation_end, mock_reminder, mock_overdue, mock_recurring
    ):
        dref = self._create_dref(appeal_code="MDRXX001", end_date=self.today)
        DrefOperationalUpdateFactory.create(
            dref=dref,
            appeal_code=dref.appeal_code,
            date_of_approval=self.today,
            new_operational_end_date=self.today
            - relativedelta(months=DREF_FINAL_REPORT_DUE_MONTHS - DREF_FINAL_REPORT_REMINDER_MONTHS_BEFORE_DUE),
        )

        call_command("dref_final_report_alert")

        mock_reminder.assert_called_once_with(dref.id)

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


class GetFinalReportAlertRecipientsTest(TestCase):
    def setUp(self):
        self.dref = DrefFactory.create(
            appeal_code="MDRXX002",
            ifrc_appeal_manager_email="dref.appeal.manager@example.com",
            ifrc_project_manager_email="dref.project.manager@example.com",
            national_society_contact_email="dref.ns.contact@example.com",
            regional_focal_point_email="dref.regional.focal@example.com",
        )

    def test_latest_approved_operational_update_is_none_when_none_exist(self):
        self.assertIsNone(get_latest_approved_operational_update(self.dref))

    def test_latest_approved_operational_update_ignores_unapproved_ones(self):
        DrefOperationalUpdateFactory.create(dref=self.dref, appeal_code=self.dref.appeal_code, date_of_approval=None)

        self.assertIsNone(get_latest_approved_operational_update(self.dref))

    def test_latest_approved_operational_update_matches_via_appeal_code_not_fk(self):
        # Deliberately attached to a different Dref to prove matching is done via appeal_code, not
        # the Operational Update's own `dref` FK.
        other_dref = DrefFactory.create(appeal_code=self.dref.appeal_code)
        operational_update = DrefOperationalUpdateFactory.create(
            dref=other_dref,
            appeal_code=self.dref.appeal_code,
            date_of_approval=timezone.now().date(),
        )

        self.assertEqual(get_latest_approved_operational_update(self.dref), operational_update)

    def test_latest_approved_operational_update_picks_most_recently_approved(self):
        today = timezone.now().date()
        DrefOperationalUpdateFactory.create(
            dref=self.dref,
            appeal_code=self.dref.appeal_code,
            date_of_approval=today - timedelta(days=10),
            operational_update_number=1,
        )
        latest = DrefOperationalUpdateFactory.create(
            dref=self.dref,
            appeal_code=self.dref.appeal_code,
            date_of_approval=today,
            operational_update_number=2,
        )

        self.assertEqual(get_latest_approved_operational_update(self.dref), latest)

    def test_recipients_fall_back_to_dref_contacts_when_no_operational_update_exists(self):
        to_emails, cc_emails = get_final_report_alert_recipients(self.dref)

        self.assertEqual(
            to_emails,
            [
                "dref.appeal.manager@example.com",
                "dref.project.manager@example.com",
                "dref.ns.contact@example.com",
            ],
        )
        self.assertEqual(cc_emails, ["dref.regional.focal@example.com"])

    def test_recipients_fall_back_to_dref_contacts_when_operational_update_is_not_approved(self):
        DrefOperationalUpdateFactory.create(
            dref=self.dref,
            appeal_code=self.dref.appeal_code,
            date_of_approval=None,
            ifrc_appeal_manager_email="ou.appeal.manager@example.com",
        )

        to_emails, _ = get_final_report_alert_recipients(self.dref)

        self.assertEqual(to_emails[0], "dref.appeal.manager@example.com")

    def test_recipients_use_approved_operational_update_contacts(self):
        DrefOperationalUpdateFactory.create(
            dref=self.dref,
            appeal_code=self.dref.appeal_code,
            date_of_approval=timezone.now().date(),
            ifrc_appeal_manager_email="ou.appeal.manager@example.com",
            ifrc_project_manager_email="ou.project.manager@example.com",
            national_society_contact_email="ou.ns.contact@example.com",
            regional_focal_point_email="ou.regional.focal@example.com",
        )

        to_emails, cc_emails = get_final_report_alert_recipients(self.dref)

        self.assertEqual(
            to_emails,
            [
                "ou.appeal.manager@example.com",
                "ou.project.manager@example.com",
                "ou.ns.contact@example.com",
            ],
        )
        self.assertEqual(cc_emails, ["ou.regional.focal@example.com"])

    def test_recipients_fall_back_per_field_when_operational_update_contact_is_blank(self):
        DrefOperationalUpdateFactory.create(
            dref=self.dref,
            appeal_code=self.dref.appeal_code,
            date_of_approval=timezone.now().date(),
            ifrc_appeal_manager_email="ou.appeal.manager@example.com",
            ifrc_project_manager_email="",
            national_society_contact_email=None,
            regional_focal_point_email="ou.regional.focal@example.com",
        )

        to_emails, cc_emails = get_final_report_alert_recipients(self.dref)

        self.assertEqual(
            to_emails,
            [
                "ou.appeal.manager@example.com",  # overridden by the Operational Update
                "dref.project.manager@example.com",  # fallback: blank on the Operational Update
                "dref.ns.contact@example.com",  # fallback: None on the Operational Update
            ],
        )
        self.assertEqual(cc_emails, ["ou.regional.focal@example.com"])

    def test_recipients_fall_back_to_dref_contacts_when_dref_has_no_appeal_code(self):
        dref = DrefFactory.create(appeal_code=None, ifrc_appeal_manager_email="dref.appeal.manager@example.com")
        DrefOperationalUpdateFactory.create(
            dref=dref,
            appeal_code=None,
            date_of_approval=timezone.now().date(),
            ifrc_appeal_manager_email="ou.appeal.manager@example.com",
        )

        to_emails, _ = get_final_report_alert_recipients(dref)

        self.assertEqual(to_emails[0], "dref.appeal.manager@example.com")
