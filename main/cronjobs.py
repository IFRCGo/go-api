"""
Registry for cronjobs scheduled by celery beat. For NEW cronjobs only.

The legacy cronjobs are k8s CronJobs listed in values.yaml:cronjobs and
monitored via main.sentry.SentryMonitor. A job belongs to one mechanism or the
other, never both -- SentryMonitor.validate_config() asserts the enum matches
values.yaml. See docs/cronjobs.md for how to add one.
"""

import functools
import logging
import operator
import typing

from celery import signals
from celery.schedules import crontab
from django.conf import settings
from django.db import models
from kombu import Queue
from sentry_sdk.integrations.celery import beat as sentry_celery_beat

if typing.TYPE_CHECKING:
    from celery import Celery
    from sentry_sdk._types import MonitorConfig

logger = logging.getLogger(__name__)


class TimeConstants:
    SECONDS_IN_A_MINUTE = 60
    SECONDS_IN_A_HOUR = 60 * 60
    SECONDS_IN_A_DAY = 24 * 60 * 60
    SECONDS_IN_A_WEEK = 7 * 24 * 60 * 60

    EVERY_WEEK = crontab(minute="1", hour="1", day_of_week="1")
    EVERY_DAY = crontab(minute="1", hour="1")
    EVERY_HOUR = crontab(minute="0", hour="*")
    EVERY_2_MINUTES = crontab(minute="*/2")
    EVERY_1_MINUTES = crontab(minute="*/1")


class CeleryQueue:
    # NOTE: Names must be lowercase (used as-is in k8s).
    default = Queue("default")
    heavy = Queue("heavy")
    cronjob = Queue("cronjob")

    # Feeds app.conf.task_queues. A worker started without -Q consumes all of these.
    ALL_QUEUE = (
        default,
        heavy,
        cronjob,
    )


class CronJobOption(typing.TypedDict, total=False):
    """Per-job options for django_celery_beat.

    WARNING: only queue/exchange/routing_key/priority/headers/expire_seconds
    survive ModelEntry._unpack_options; anything else is silently dropped. Put
    time_limit/soft_time_limit on the task decorator instead.
    """

    expire_seconds: float
    """Task will not run if picked up later than this. Avoids a backlog when workers are down."""

    queue: str
    """Queue the task is sent to. Required -- see test_cronjobs.py."""


class CeleryBeatSchedule(typing.TypedDict):
    task: str
    schedule: crontab
    options: CronJobOption
    args: tuple[typing.Any, ...]


class CronJobSentryConfig(typing.NamedTuple):
    checkin_margin: int = 5
    """Minutes of grace before a missed check-in is flagged."""

    max_runtime: int = 30
    """Minutes before Sentry considers the job failed."""

    failure_issue_threshold: int = 1
    """Consecutive failures before an issue is created."""

    recovery_threshold: int = 1
    """Consecutive successes before an issue is resolved."""

    def as_dict(self) -> "MonitorConfig":
        return {
            "checkin_margin": self.checkin_margin,
            "max_runtime": self.max_runtime,
            "failure_issue_threshold": self.failure_issue_threshold,
            "recovery_threshold": self.recovery_threshold,
        }


class CronJob(typing.NamedTuple):
    task: str
    schedule: crontab
    args: tuple[typing.Any, ...] = ()
    sentry_config: CronJobSentryConfig = CronJobSentryConfig()
    options: CronJobOption = {}


# NOTE: Removing an entry here deletes its PeriodicTask row (see update_periodic_tasks).
SCHEDULES: dict[str, CronJob] = {
    "clear_expired_django_sessions": CronJob(
        task="api.tasks.clear_expired_django_sessions",
        schedule=TimeConstants.EVERY_WEEK,
        options=CronJobOption(expire_seconds=TimeConstants.SECONDS_IN_A_WEEK),
    ),
    **{
        f"celery_queue_uptime_{celery_queue.name}": CronJob(
            task="api.tasks.celery_queue_uptime_check",
            args=(celery_queue.name,),
            schedule=TimeConstants.EVERY_HOUR,
            options=CronJobOption(
                expire_seconds=TimeConstants.SECONDS_IN_A_HOUR,
                queue=celery_queue.name,
            ),
            sentry_config=CronJobSentryConfig(
                checkin_margin=10,
                max_runtime=2,
                failure_issue_threshold=2,
            ),
        )
        for celery_queue in CeleryQueue.ALL_QUEUE
    },
}

BEAT_SCHEDULES: dict[str, CeleryBeatSchedule] = {
    name: {
        "task": config.task,
        "args": config.args,
        "schedule": config.schedule,
        "options": config.options,
    }
    for name, config in SCHEDULES.items()
}


_get_monitor_config = sentry_celery_beat._get_monitor_config


class SentryMonkeyPatch:
    @staticmethod
    def custom__get_monitor_config(celery_schedule: typing.Any, app: "Celery", monitor_name: str) -> "MonitorConfig":
        """Get configuration for sentry monitoring.

        https://github.com/getsentry/sentry-python/blob/5715734eac1c5fb4b6ec61ef459080c74fa777b5/sentry_sdk/integrations/celery/beat.py#L59
        """
        config = _get_monitor_config(celery_schedule, app, monitor_name)
        job_config = SCHEDULES.get(monitor_name)
        if job_config:
            config.update(job_config.sentry_config.as_dict())
        return config


sentry_celery_beat._get_monitor_config = SentryMonkeyPatch.custom__get_monitor_config


def get_obsolete_periodic_task_qs():
    """Our PeriodicTask rows that are no longer in SCHEDULES.

    Scoped to GO_APPS so third-party rows are never touched. `manual:` rows are
    spared as an escape hatch for one-off tasks created in the admin.
    """
    from django_celery_beat.models import PeriodicTask

    ours = functools.reduce(
        operator.or_,
        [models.Q(task__startswith=f"{app_name}.") for app_name in settings.GO_APPS],
    )

    return PeriodicTask.objects.filter(ours).exclude(name__in=list(BEAT_SCHEDULES.keys())).exclude(name__startswith="manual:")


@signals.beat_init.connect
def update_periodic_tasks(**_):
    """Drop rows for cronjobs no longer in SCHEDULES -- git is the source of truth."""
    logger.info("Cronjob sync: Start")
    try:
        obsolete_tasks_qs = get_obsolete_periodic_task_qs()

        obsolete_task_names = list(obsolete_tasks_qs.values_list("name", flat=True))
        if not obsolete_task_names:
            logger.info("Cronjob sync - Obsolete tasks: Nothing to do")
            return

        for task_name in obsolete_task_names:
            logger.warning("Cronjob sync - Obsolete tasks: Task <%s> will be deleted", task_name)

        deleted_count, _ = obsolete_tasks_qs.delete()
        logger.warning("Cronjob sync - Obsolete tasks: Deleted %s tasks", deleted_count)
    except Exception:
        logger.error("Cronjob sync: Failed to sync PeriodicTasks", exc_info=True)
