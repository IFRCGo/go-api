import shlex
import subprocess

from django.core.management.base import BaseCommand
from django.utils.autoreload import run_with_reloader

from main.celery import Queues


all_queues = ','.join([q for q in Queues.DEV_QUEUES])
CMD = (
    f'celery -A main worker -Q {all_queues} '
    '-B --concurrency=2 -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler'
)


def restart_celery():
    kill_worker_cmd = 'pkill -9 celery'
    subprocess.call(shlex.split(kill_worker_cmd))
    subprocess.call(shlex.split(CMD))


class Command(BaseCommand):
    requires_system_checks = []

    def handle(self, *args, **options):
        self.stdout.write('Starting celery worker with autoreload...')
        run_with_reloader(restart_celery)
