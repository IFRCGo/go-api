import os
#ς import celery
#ς : this greek sigma (ς) shows the celery-comments everywhere


#ς class Celery(celery.Celery):
#ς     pass


# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")

#ς app = Celery('main')

#ς # Using a string here means the worker doesn't have to serialize
#ς # the configuration object to child processes.
#ς # - namespace='CELERY' means all celery-related configuration keys
#ς #   should have a `CELERY_` prefix.
#ς app.config_from_object('django.conf:settings', namespace='CELERY')

#ς # Load task modules from all registered Django app configs.
#ς app.autodiscover_tasks()


class Queues():
    DEFAULT = 'default'
    HEAVY = 'heavy'
    CRONJOB = 'cronjob'

    DEV_QUEUES = (
        DEFAULT,
        HEAVY,
        CRONJOB,
    )


#ς @app.task(bind=True)
#ς def debug_task(self):
#ς     print('Request: {0!r}'.format(self.request))
