# Cronjobs

There are **two** cronjob mechanisms. Use celery beat for new cronjobs.

A job belongs to one mechanism or the other, **never both** —
`SentryMonitor.validate_config()` asserts that the enum matches `values.yaml`,
so mixing them breaks it.

## 1. Celery beat — use this for new cronjobs

Schedules are declared in [`main/cronjobs.py`](../main/cronjobs.py) and synced
into `django_celery_beat` `PeriodicTask` rows when beat starts. `SCHEDULES` is
the source of truth: remove an entry and its row is deleted on the next start.
Rows named `manual:*` are left alone, as an escape hatch for one-off tasks
created through the admin.

Adding one takes two files, with no helm change and no `cron_job_monitor` run:

**1. Write the task in `<app>/tasks.py`**

```python
@shared_task(soft_time_limit=..., time_limit=...)
def my_new_job():
    with redis_lock(RedisLockKey.MY_NEW_JOB) as acquired:
        if not acquired:
            return
        ...
```

- The lock matters: `CELERY_ACKS_LATE` is on, so a task can be redelivered to
  another worker if the one running it dies.
- Time limits go **on the decorator**. `DatabaseScheduler` silently discards
  `time_limit` / `soft_time_limit` from a schedule entry's options.
- Don't set `queue` here — it belongs in the schedule entry below.

**2. Add a `CronJob` entry to `SCHEDULES` in `main/cronjobs.py`**

```python
"my_new_job": CronJob(
    task="myapp.tasks.my_new_job",
    schedule=TimeConstants.EVERY_DAY,
    options=CronJobOption(
        expire_seconds=TimeConstants.SECONDS_IN_A_DAY,
        queue=CeleryQueue.cronjob.name,
    ),
    sentry_config=CronJobSentryConfig(max_runtime=10),
),
```

`options` only supports the keys `ModelEntry._unpack_options` keeps — `queue`,
`exchange`, `routing_key`, `priority`, `headers`, `expire_seconds`. Anything
else is dropped without warning. `expire_seconds` stops a backlog accumulating
while workers are down.

Sentry cron monitoring is automatic, controlled by
`SENTRY_MONITOR_CELERY_BEAT_TASKS` (default on). `CronJobSentryConfig` sets each
job's grace period, max runtime and thresholds next to its schedule.

### Queues

`CeleryQueue` in `main/cronjobs.py` declares which queues exist (`default`,
`heavy`, `cronjob`) and feeds `app.conf.task_queues`. A worker started without
`-Q` consumes all of them, which is the dev setup.

A queue that is routed to but not declared here is a black hole: the task is
accepted and then never consumed by anything.

### Running locally

```bash
docker-compose up celery celery-beat
```

Worker and beat entrypoints live in `misc/dev/`. Both wait for the database and
the broker first via banjo's `manage.py wait_for_resources`.

### Deployment

Beat runs as the `beat` worker addon in
[`deploy/helm/values.yaml`](../deploy/helm/values.yaml) (`app.worker.addons.beat`),
rendered by banjo-helm as a `-worker-beat` Deployment.

Two properties there are load-bearing:

- **`replicaCount: 1` with `strategy: Recreate`.** Two beat processes fire every
  cronjob twice, so this must never be scaled up.
- **`--scheduler=banjo_utils.celery_health.database.HeartbeatDatabaseScheduler`** —
  django-celery-beat's `DatabaseScheduler` plus a heartbeat file each tick, which
  is what the `banjo-celery-probe` liveness check reads.

Beat needs the `django_celery_beat` tables, created by `manage.py migrate` in the
deploy hook. If beat starts first it crashloops until migrations have run.

After changing `SCHEDULES`, regenerate the chart snapshots:

```bash
cd deploy/helm && ./update-snapshots.sh
```

## 2. Kubernetes CronJobs — the legacy set

The pre-existing cronjobs run as k8s CronJob resources listed under
`app.cronjobs.jobs` in `deploy/helm/values.yaml`, one pod per run, monitored via
`SentryMonitor` in `main/sentry.py`. Their Sentry monitors are **not** created
automatically — they must be registered per environment with:

```bash
docker-compose exec serve bash ./manage.py cron_job_monitor
```
