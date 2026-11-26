import enum
import logging
import os
import typing
from difflib import context_diff

import sentry_sdk
import yaml

# Celery Terminated Exception: The worker processing a job has been terminated by user request.
from billiard.exceptions import Terminated
from celery.exceptions import Retry as CeleryRetry
from django.conf import settings
from django.core.exceptions import PermissionDenied
from sentry_sdk.crons import monitor
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import ignore_logger
from sentry_sdk.integrations.redis import RedisIntegration

if typing.TYPE_CHECKING:
    from sentry_sdk._types import MonitorConfig

IGNORED_ERRORS = [
    Terminated,
    PermissionDenied,
    CeleryRetry,
]
IGNORED_LOGGERS = [
    "django.core.exceptions.ObjectDoesNotExist",
]

logger = logging.getLogger(__name__)

for _logger in IGNORED_LOGGERS:
    ignore_logger(_logger)


class InvalidGitRepository(Exception):
    pass


def fetch_git_sha(path, head=None):
    """
    Source: https://github.com/getsentry/raven-python/blob/03559bb05fd963e2be96372ae89fb0bce751d26d/raven/versioning.py
    >>> fetch_git_sha(os.path.dirname(__file__))
    """
    if not head:
        head_path = os.path.join(path, ".git", "HEAD")
        if not os.path.exists(head_path):
            raise InvalidGitRepository("Cannot identify HEAD for git repository at %s" % (path,))

        with open(head_path, "r") as fp:
            head = str(fp.read()).strip()

        if head.startswith("ref: "):
            head = head[5:]
            revision_file = os.path.join(path, ".git", *head.split("/"))
        else:
            return head
    else:
        revision_file = os.path.join(path, ".git", "refs", "heads", head)

    if not os.path.exists(revision_file):
        if not os.path.exists(os.path.join(path, ".git")):
            raise InvalidGitRepository("%s does not seem to be the root of a git repository" % (path,))

        # Check for our .git/packed-refs' file since a `git gc` may have run
        # https://git-scm.com/book/en/v2/Git-Internals-Maintenance-and-Data-Recovery
        packed_file = os.path.join(path, ".git", "packed-refs")
        if os.path.exists(packed_file):
            with open(packed_file) as fh:
                for line in fh:
                    line = line.rstrip()
                    if line and line[:1] not in ("#", "^"):
                        try:
                            revision, ref = line.split(" ", 1)
                        except ValueError:
                            continue
                        if ref == head:
                            return str(revision)

        raise InvalidGitRepository('Unable to find ref to head "%s" in repository' % (head,))

    with open(revision_file) as fh:
        return str(fh.read()).strip()


def init_sentry(app_type, tags={}, **config):
    integrations = [
        CeleryIntegration(),
        DjangoIntegration(),
        RedisIntegration(),
    ]
    sentry_sdk.init(
        **config,
        ignore_errors=IGNORED_ERRORS,
        integrations=integrations,
    )
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("app_type", app_type)
        for tag, value in tags.items():
            scope.set_tag(tag, value)


class CronJobSentryConfig(typing.NamedTuple):
    """
    Sentry monitor config for a cronjob
    https://docs.sentry.io/platforms/python/crons/
    """

    slug: str
    """Monitor slug, same as the management command name and the values.yaml job key."""

    schedule: str
    """Crontab schedule, same as values.yaml."""

    checkin_margin: int = 15
    """
    The amount of time (in minutes) Sentry should wait for your check-in before it's considered missed ("grace period").
    """

    max_runtime: int = 30
    """The amount of time (in minutes) your job is allowed to run before it's considered failed."""

    failure_issue_threshold: int = 1
    """The number of consecutive failed check-ins it takes before an issue is created."""

    recovery_threshold: int = 1
    """The number of consecutive OK check-ins it takes before an issue is resolved."""

    def as_dict(self) -> "MonitorConfig":
        return {
            "schedule": {
                "type": "crontab",
                "value": self.schedule,
            },
            "timezone": settings.TIME_ZONE,
            "checkin_margin": self.checkin_margin,
            "max_runtime": self.max_runtime,
            "failure_issue_threshold": self.failure_issue_threshold,
            "recovery_threshold": self.recovery_threshold,
        }


class SentryMonitor(enum.Enum):
    """
    Sentry cron monitors of cron jobs
    @Note: Before adding the jobs to this class, make sure to add the job to the `Values.yaml` file
    """

    # NOTE: Runs every 5 minutes; we allow up to 6 consecutive failures
    INDEX_AND_NOTIFY = CronJobSentryConfig("index_and_notify", "*/5 * * * *", failure_issue_threshold=6)
    # NOTE: Takes longer than the default max runtime
    SYNC_MOLNIX = CronJobSentryConfig("sync_molnix", "10 */2 * * *", max_runtime=40)
    INGEST_APPEALS = CronJobSentryConfig("ingest_appeals", "*/30 * * * *")
    SYNC_APPEALDOCS = CronJobSentryConfig("sync_appealdocs", "15 * * * *")
    REVOKE_STAFF_STATUS = CronJobSentryConfig("revoke_staff_status", "51 * * * *")
    UPDATE_PROJECT_STATUS = CronJobSentryConfig("update_project_status", "1 3 * * *")
    USER_REGISTRATION_REMINDER = CronJobSentryConfig("user_registration_reminder", "0 9 * * *")
    INGEST_COUNTRY_PLAN_FILE = CronJobSentryConfig("ingest_country_plan_file", "1 0 * * *")
    FDRS_ANNUAL_INCOME = CronJobSentryConfig("fdrs_annual_income", "0 0 * * 0")
    FDRS_INCOME = CronJobSentryConfig("FDRS_INCOME", "0 0 * * 0")
    INGEST_ACAPS = CronJobSentryConfig("ingest_acaps", "0 1 * * 0")
    INGEST_CLIMATE = CronJobSentryConfig("ingest_climate", "0 0 * * 0")
    INGEST_DATABANK = CronJobSentryConfig("ingest_databank", "0 0 * * 0")
    INGEST_HDR = CronJobSentryConfig("ingest_hdr", "0 0 * * 0")
    INGEST_UNICEF = CronJobSentryConfig("ingest_unicef", "0 0 * * 0")
    INGEST_WORLDBANK = CronJobSentryConfig("ingest_worldbank", "0 2 * * 0")
    INGEST_DISASTER_LAW = CronJobSentryConfig("ingest_disaster_law", "0 0 * * 0")
    INGEST_NS_CONTACT = CronJobSentryConfig("ingest_ns_contact", "0 0 * * 0")
    INGEST_NS_CAPACITY = CronJobSentryConfig("ingest_ns_capacity", "0 0 * * 0")
    INGEST_NS_DIRECTORY = CronJobSentryConfig("ingest_ns_directory", "0 0 * * 0")
    INGEST_NS_DOCUMENT = CronJobSentryConfig("ingest_ns_document", "0 0 * * 0")
    INGEST_NS_INITIATIVES = CronJobSentryConfig("ingest_ns_initiatives", "0 0 * * 0")
    INGEST_ICRC = CronJobSentryConfig("ingest_icrc", "0 3 * * 0")
    NOTIFY_VALIDATORS = CronJobSentryConfig("notify_validators", "0 0 * * *")
    POLL_USGS_EARTHQUAKE = CronJobSentryConfig("poll_usgs_earthquake", "0 18 * * 0")
    POLL_GDACS_FLOOD = CronJobSentryConfig("poll_gdacs_flood", "0 11 * * *")
    POLL_GDACS_CYCLONE = CronJobSentryConfig("poll_gdacs_cyclone", "0 11 * * 0")
    OAUTH_CLEARTOKENS = CronJobSentryConfig("oauth_cleartokens", "0 1 * * *")
    EAP_SUBMISSION_REMINDER = CronJobSentryConfig("eap_submission_reminder", "0 0 * * *")
    ALERT_NOTIFICATION = CronJobSentryConfig("alert_notification", "0 */2 * * *")
    DREF_FINAL_REPORT_ALERT = CronJobSentryConfig("dref_final_report_alert", "0 6 * * *")

    @staticmethod
    def load_cron_data() -> typing.List[typing.Tuple[str, str]]:
        with open(os.path.join(settings.BASE_DIR, "deploy/helm/values.yaml")) as fp:
            try:
                # Helm chart cronjobs are keyed by the management-command name under
                # app.cronjobs.jobs.<name> = {schedule, command}. Keep the job keys in
                # sync with the SentryMonitor members (slug == command).
                jobs = yaml.safe_load(fp)["app"]["cronjobs"]["jobs"]
                return [(name, metadata["schedule"]) for name, metadata in jobs.items()]
            except yaml.YAMLError as e:
                logger.error("Failed to load cronjob data from helm", exc_info=True)
                raise e

    @classmethod
    def validate_config(cls):
        """
        Validate SentryMonitor task list with Helm
        """
        current_crons = {(job.value.slug, job.value.schedule) for job in cls}
        current_helm_crons = set(cls.load_cron_data())
        assert current_crons == current_helm_crons, (
            # Show a simple diff for correction
            "SentryMonitor needs update\n\n"
            + (
                "\n".join(
                    list(
                        context_diff(
                            sorted(f"{c} {s}" for c, s in current_crons),
                            sorted(f"{c} {s}" for c, s in current_helm_crons),
                            fromfile="SentryMonitor",
                            tofile="Values.yml",
                        )
                    )
                )
            )
        )


def sentry_cron_monitor(job: SentryMonitor):
    """
    Wrap sentry_sdk.crons.monitor with the monitor_config, so Sentry creates/updates
    the monitor on check-in.
    """

    def decorator(func):
        wrapped = monitor(monitor_slug=job.value.slug, monitor_config=job.value.as_dict())(func)
        # Used by tests to verify each SentryMonitor command is monitored
        wrapped.sentry_monitor = job
        return wrapped

    return decorator
