from django.core.management import get_commands, load_command_class
from django.test import SimpleTestCase

from main.sentry import SentryMonitor, SentryMonitorConfig


class SentryMonitorConfigTest(SimpleTestCase):
    def test_get_monitor_config(self):
        config = SentryMonitorConfig.get_monitor_config(SentryMonitor.DREF_FINAL_REPORT_ALERT)
        self.assertEqual(
            config,
            {
                "schedule": {"type": "crontab", "value": "0 6 * * *"},
                "timezone": "UTC",
                "checkin_margin": 5,
                "max_runtime": 30,
                "failure_issue_threshold": 1,
                "recovery_threshold": 1,
            },
        )

    def test_failure_threshold_override(self):
        config = SentryMonitorConfig.get_monitor_config(SentryMonitor.INDEX_AND_NOTIFY)
        self.assertEqual(config["failure_issue_threshold"], 6)

    def test_commands_use_sentry_cron_monitor(self):
        commands = get_commands()
        for enum in SentryMonitor:
            with self.subTest(command=enum.value):
                command = load_command_class(commands[enum.value], enum.value)
                self.assertEqual(getattr(command.handle, "sentry_monitor", None), enum)
