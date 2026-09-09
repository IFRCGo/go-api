import dataclasses
import inspect
from pydoc import locate

import pytest
from django.conf import settings

from main import cronjobs
from main.cronjobs import (
    BEAT_SCHEDULES,
    SCHEDULES,
    CeleryQueue,
    SentryMonkeyPatch,
    get_obsolete_periodic_task_qs,
)

ALL_QUEUE_NAMES = {queue.name for queue in CeleryQueue.ALL_QUEUE}

# SentryConfig fields that are ours, not sentry_sdk.init() options.
CUSTOM_SENTRY_FIELDS = {"monitor_celery_beat_tasks", "app_type", "tags"}

# The only keys ModelEntry._unpack_options keeps; anything else is silently dropped.
SUPPORTED_OPTION_KEYS = {
    "queue",
    "exchange",
    "routing_key",
    "priority",
    "headers",
    "expire_seconds",
}


def test_sentry_config_fields_are_all_accounted_for():
    """Each SentryConfig field must be a real sentry_sdk option or a known custom one.

    sentry_sdk.init() raises `TypeError: Unknown option` for anything it does not
    recognise, and that only happens once SENTRY_DSN is set -- never locally.
    A field that is neither must be handled by hand in init_sentry().
    """
    from sentry_sdk.consts import DEFAULT_OPTIONS

    from main.sentry import SentryConfig

    fields = {f.name for f in dataclasses.fields(SentryConfig)}
    unaccounted = fields - set(DEFAULT_OPTIONS) - CUSTOM_SENTRY_FIELDS
    assert not unaccounted, f"SentryConfig fields sentry_sdk.init() does not know: {unaccounted}"


def test_sentry_config_still_carries_beat_monitoring():
    assert isinstance(settings.SENTRY_CONFIG.monitor_celery_beat_tasks, bool)
    assert dataclasses.replace(settings.SENTRY_CONFIG, app_type="WORKER").app_type == "WORKER"


def test_schedules_tasks_are_importable_celery_tasks():
    for name, config in SCHEDULES.items():
        task = locate(config.task)
        assert task is not None, f"{name}: task path does not exist: {config.task}"
        assert hasattr(task, "delay"), f"{name}: {config.task} is not a celery task"


def test_schedules_set_the_queue_in_config_not_on_the_task():
    """A queue is optional -- without one the task uses task_default_queue. When
    it is set it belongs in the SCHEDULES entry, never on the task decorator.
    """
    for name, config in SCHEDULES.items():
        task_queue = getattr(locate(config.task), "queue", None)
        assert task_queue is None, f"{name}: set queue in SCHEDULES, not on the {config.task} decorator"

        queue = config.options.get("queue")
        if queue is not None:
            assert queue in ALL_QUEUE_NAMES, f"{name}: queue {queue!r} is not one of {ALL_QUEUE_NAMES}"


def test_schedules_declare_an_expiry():
    """Without expire_seconds a backlog accumulates while workers are down."""
    missing = [name for name, config in SCHEDULES.items() if "expire_seconds" not in config.options]
    assert not missing, f"Cronjobs missing expire_seconds: {missing}"


def test_schedules_only_use_options_the_scheduler_honours():
    """Guard against silently-dropped options (eg. time_limit belongs on the task)."""
    for name, entry in BEAT_SCHEDULES.items():
        unsupported = set(entry["options"]) - SUPPORTED_OPTION_KEYS
        assert not unsupported, f"{name}: options {unsupported} are ignored by DatabaseScheduler"


def test_prune_filter_matches_how_our_tasks_are_named():
    """A task path not starting with a GO_APPS label is invisible to pruning."""
    for name, config in SCHEDULES.items():
        app_label = config.task.split(".")[0]
        assert app_label in settings.GO_APPS, f"{name}: {config.task} does not start with a GO_APPS label"


def test_sentry_monkeypatch_is_applied_and_signature_still_matches():
    """Fails if a sentry-sdk upgrade moves or re-signatures the private hook."""
    from sentry_sdk.integrations.celery import beat as sentry_celery_beat

    assert sentry_celery_beat._get_monitor_config is SentryMonkeyPatch.custom__get_monitor_config

    expected = ["celery_schedule", "app", "monitor_name"]
    assert list(inspect.signature(cronjobs._get_monitor_config).parameters) == expected
    assert list(inspect.signature(SentryMonkeyPatch.custom__get_monitor_config).parameters) == expected


@pytest.mark.django_db
def test_prune_targets_only_obsolete_rows_of_ours():
    from django_celery_beat.models import IntervalSchedule, PeriodicTask

    schedule, _ = IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.DAYS)

    PeriodicTask.objects.create(name="obsolete_job", task="api.tasks.removed_job", interval=schedule)
    # Spared: deliberate admin-created escape hatch.
    PeriodicTask.objects.create(name="manual:adhoc_job", task="api.tasks.removed_job", interval=schedule)
    # Spared: not one of our apps.
    PeriodicTask.objects.create(name="vendor_job", task="some_vendor.tasks.thing", interval=schedule)
    # Spared: still declared in SCHEDULES.
    PeriodicTask.objects.create(
        name="clear_expired_django_sessions",
        task="api.tasks.clear_expired_django_sessions",
        interval=schedule,
    )

    assert set(get_obsolete_periodic_task_qs().values_list("name", flat=True)) == {"obsolete_job"}
