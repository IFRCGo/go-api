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
from django.db import models
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import ignore_logger
from sentry_sdk.integrations.redis import RedisIntegration

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


class SentryMonitor(models.TextChoices):
    """
    This class is used to create Sentry monitor of cron jobs
    @Note: Before adding the jobs to this class, make sure to add the job to the `Values.yaml` file
    """

    INDEX_AND_NOTIFY = "index_and_notify", "*/5 * * * *"
    SYNC_MOLNIX = "sync_molnix", "10 */2 * * *"
    INGEST_APPEALS = "ingest_appeals", "*/30 * * * *"
    SYNC_APPEALDOCS = "sync_appealdocs", "15 * * * *"
    REVOKE_STAFF_STATUS = "revoke_staff_status", "51 * * * *"
    UPDATE_PROJECT_STATUS = "update_project_status", "1 3 * * *"
    USER_REGISTRATION_REMINDER = "user_registration_reminder", "0 9 * * *"
    INGEST_COUNTRY_PLAN_FILE = "ingest_country_plan_file", "1 0 * * *"
    FDRS_ANNUAL_INCOME = "fdrs_annual_income", "0 0 * * 0"
    FDRS_INCOME = "FDRS_INCOME", "0 0 * * 0"
    INGEST_ACAPS = "ingest_acaps", "0 1 * * 0"
    INGEST_CLIMATE = "ingest_climate", "0 0 * * 0"
    INGEST_DATABANK = "ingest_databank", "0 0 * * 0"
    INGEST_HDR = "ingest_hdr", "0 0 * * 0"
    INGEST_UNICEF = "ingest_unicef", "0 0 * * 0"
    INGEST_WORLDBANK = "ingest_worldbank", "0 2 * * 0"
    INGEST_DISASTER_LAW = "ingest_disaster_law", "0 0 * * 0"
    INGEST_NS_CONTACT = "ingest_ns_contact", "0 0 * * 0"
    INGEST_NS_CAPACITY = "ingest_ns_capacity", "0 0 * * 0"
    INGEST_NS_DIRECTORY = "ingest_ns_directory", "0 0 * * 0"
    INGEST_NS_DOCUMENT = "ingest_ns_document", "0 0 * * 0"
    INGEST_NS_INITIATIVES = "ingest_ns_initiatives", "0 0 * * 0"
    INGEST_ICRC = "ingest_icrc", "0 3 * * 0"
    POLL_USGS_EQ = "poll_usgs_eq", "0 0 * * 0"
    POLL_GDACS_FL = "poll_gdacs_fl", "0 0 * * 0"
    POLL_GDACS_CY = "poll_gdacs_cy", "0 0 * * 0"
    # NOTIFY_VALIDATORS = "notify_validators", "0 0 * * *" # NOTE: Disable local unit email notification for now
    OAUTH_CLEARTOKENS = "oauth_cleartokens", "0 1 * * *"

    @staticmethod
    def load_cron_data() -> typing.List[typing.Tuple[str, str]]:
        with open(os.path.join(settings.BASE_DIR, "deploy/helm/ifrcgo-helm/values.yaml")) as fp:
            try:
                return [(metadata["command"], metadata["schedule"]) for metadata in yaml.safe_load(fp)["cronjobs"]]
            except yaml.YAMLError as e:
                logger.error("Failed to load cronjob data from helm", exc_info=True)
                raise e

    @classmethod
    def validate_config(cls):
        """
        Validate SentryMonitor task list with Helm
        """
        current_helm_crons = cls.load_cron_data()
        assert set(cls.choices) == set(current_helm_crons), (
            # Show a simple diff for correction
            "SentryMonitor needs update\n\n"
            + (
                "\n".join(
                    list(
                        context_diff(
                            [f"{c} {s}" for c, s in set(cls.choices)],
                            [f"{c} {s}" for c, s in set(current_helm_crons)],
                            fromfile="SentryMonitor",
                            tofile="Values.yml",
                        )
                    )
                )
            )
        )


class SentryMonitorConfig:
    """
    Custom config for SentryMonitor
    https://docs.sentry.io/product/crons/getting-started/http/#creating-or-updating-a-monitor-through-a-check-in-optional
    """

    MAX_RUNTIME_DEFAULT = 30  # Our default is 30 min

    FAILURE_THRESHOLD_DEFAULT = 1
    FAILURE_THRESHOLD = {
        # NOTE: INDEX_AND_NOTIFY runs every 5 minutes; we allow up to 6 consecutive failures
        SentryMonitor.INDEX_AND_NOTIFY: 6,
    }

    @classmethod
    def get_checkin_margin(cls, _: SentryMonitor) -> int:
        """
        The amount of time (in minutes) [Sentry Default 1 min]
        Sentry should wait for your checkin before it's considered missed ("grace period")
        """
        return cls.MAX_RUNTIME_DEFAULT

    @classmethod
    def get_failure_issue_threshold(cls, enum: SentryMonitor) -> int:
        """
        The number of consecutive failed check-ins it takes before an issue is created. Optional.
        """
        return cls.FAILURE_THRESHOLD.get(enum, cls.FAILURE_THRESHOLD_DEFAULT)

    @classmethod
    def get_recovery_threshold(cls, _: SentryMonitor) -> int:
        """
        [Sentry Default 1]
        The number of consecutive OK check-ins it takes before an issue is resolved. Optional.
        """
        return 1
