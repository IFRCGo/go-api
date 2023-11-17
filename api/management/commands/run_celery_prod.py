import typing
import shlex
import subprocess
import argparse

from django.core.management.base import BaseCommand

from main.celery import Queues


all_queues = ",".join([q for q in Queues.DEV_QUEUES])


def get_celery_cmd(
    queues: str,
    celery_args: typing.Union[None, typing.List[str]] = None,
):
    cmd = f"celery -A main worker -Q {queues} -l info"
    if celery_args:
        cmd = f"{cmd} {' '.join(celery_args)}"
    return cmd


class Command(BaseCommand):
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument(
            '--queues',
            type=str,
            default=all_queues,
            help=f'Name of the queues seperated by comma: Default is {all_queues}',
        )
        parser.add_argument(
            '--celery-args',
            help='All the argument after this are passed to celery',
            nargs=argparse.REMAINDER,
            default=None,
        )

    def handle(self, *_, **options):
        queues = options['queues']
        celery_args = options['celery_args']
        cmd = get_celery_cmd(queues, celery_args)
        self.stdout.write(f"Starting celery worker... {cmd}")
        subprocess.call(shlex.split(cmd))
