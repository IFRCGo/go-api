import os

import celery
from banjo_utils.celery_health.worker import setup_worker_heartbeat
from django.conf import settings

from main import sentry


class CustomCeleryApp(celery.Celery):
    def on_configure(self):
        if settings.SENTRY_DSN:
            sentry.init_sentry(
                app_type="WORKER",
                **settings.SENTRY_CONFIG,
            )


# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")

app = CustomCeleryApp("main")
# Write a periodic heartbeat file so the worker pod's liveness probe
# (banjo-celery-probe) can tell the worker is processing.
setup_worker_heartbeat(app)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


class Queues:
    DEFAULT = "default"
    HEAVY = "heavy"
    CRONJOB = "cronjob"

    DEV_QUEUES = (
        DEFAULT,
        HEAVY,
        CRONJOB,
    )


app.conf.task_default_queue = Queues.DEFAULT


@app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))
