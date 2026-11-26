from unittest import mock

from django.core.management import get_commands, load_command_class
from django.test import SimpleTestCase

from main.sentry import SentryMonitor, sentry_cron_monitor


class SentryMonitorTest(SimpleTestCase):
    def test_as_dict(self):
        self.assertEqual(
            SentryMonitor.DREF_FINAL_REPORT_ALERT.value.as_dict(),
            {
                "schedule": {"type": "crontab", "value": "0 6 * * *"},
                "timezone": "UTC",
                "checkin_margin": 15,
                "max_runtime": 30,
                "failure_issue_threshold": 1,
                "recovery_threshold": 1,
            },
        )

    def test_validate_config(self):
        SentryMonitor.validate_config()

    def test_commands_use_sentry_cron_monitor(self):
        commands = get_commands()
        for job in SentryMonitor:
            with self.subTest(command=job.value.slug):
                command = load_command_class(commands[job.value.slug], job.value.slug)
                self.assertEqual(getattr(command.handle, "sentry_monitor", None), job)

    @mock.patch("sentry_sdk.crons.decorator.capture_checkin")
    def test_sentry_cron_monitor(self, capture_checkin):
        job = SentryMonitor.DREF_FINAL_REPORT_ALERT
        sentry_cron_monitor(job)(lambda: None)()

        checkin = capture_checkin.call_args.kwargs
        self.assertEqual(checkin["monitor_slug"], "dref_final_report_alert")
        self.assertEqual(checkin["monitor_config"], job.value.as_dict())
        self.assertEqual(checkin["status"], "ok")
