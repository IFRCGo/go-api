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

Worker and beat entrypoints live in `misc/dev/`.

### Not deployed yet

**Beat currently runs in local development only.** There is no beat Deployment
in `deploy/helm/`, so nothing in `SCHEDULES` fires in alpha/staging/prod until
one is added. Still to do:

- A beat Deployment with **`replicas: 1`** and `strategy: Recreate` — two beat
  processes fire every cronjob twice — plus a `celeryBeat` block in
  `values.yaml`. It needs the same `envFrom` secret + configmap as the celery
  worker.
- Beat needs the `django_celery_beat` tables, which `manage.py migrate` creates
  on the API pod. If beat starts first it crashloops until migrations have run.

## 2. Kubernetes CronJobs — the legacy set

The pre-existing cronjobs run as k8s CronJob resources listed under `cronjobs:`
in `deploy/helm/ifrcgo-helm/values.yaml`, one pod per run, monitored via
`SentryMonitor` in `main/sentry.py`. Their Sentry monitors are registered with:

```bash
docker-compose exec serve bash ./manage.py cron_job_monitor
```
