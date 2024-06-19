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
    SYNC_MOLNIX = "sync_molnix", "*/15 * * * *"
    INGEST_APPEALS = "ingest_appeals", "45 */2 * * *"
    SYNC_APPEALDOCS = "sync_appealdocs", "15 * * * *"
    REVOKE_STAFF_STATUS = "revoke_staff_status", "51 * * * *"
    UPDATE_PROJECT_STATUS = "update_project_status", "1 3 * * *"
    USER_REGISTRATION_REMINDER = "user_registration_reminder", "0 9 * * *"
    INGEST_COUNTRY_PLAN_FILE = "ingest_country_plan_file", "1 0 * * *"
    UPDATE_SURGE_ALERT_STATUS = "update_surge_alert_status", "1 */12 * * *"

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
