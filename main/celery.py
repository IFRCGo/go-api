import dataclasses
import os

import celery
from django.conf import settings

from main.cronjobs import BEAT_SCHEDULES, CeleryQueue


class CustomCeleryApp(celery.Celery):
    def on_configure(self):
        if settings.SENTRY_DSN:
            dataclasses.replace(settings.SENTRY_CONFIG, app_type="WORKER").init_sentry()


# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")

app = CustomCeleryApp("main")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


app.conf.task_default_queue = CeleryQueue.default.name
app.conf.task_queues = CeleryQueue.ALL_QUEUE

# Cronjobs scheduled through celery beat. See main/cronjobs.py -- note that this
# is separate from the legacy k8s CronJob resources in values.yaml:cronjobs.
app.conf.beat_schedule = BEAT_SCHEDULES


@app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))
