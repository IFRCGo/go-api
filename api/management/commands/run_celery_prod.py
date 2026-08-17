import argparse
import shlex
import subprocess
import typing

from django.core.management.base import BaseCommand

from main.cronjobs import CeleryQueue

all_queues = ",".join([q.name for q in CeleryQueue.ALL_QUEUE])

# NOTE: Use a fixed concurrency to prevent the pod from being OOMKilled,
# as Celery defaults to one worker per available CPU.


def get_celery_cmd(
    queues: str,
    concurrency: int,
    celery_args: typing.Union[None, typing.List[str]] = None,
):
    cmd = f"celery -A main worker " f"-Q {queues} " f"-l info " f"--concurrency={concurrency}"

    if celery_args:
        cmd = f"{cmd} {' '.join(celery_args)}"
    return cmd


class Command(BaseCommand):
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument(
            "--queues",
            type=str,
            default=all_queues,
            help=f"Name of the queues seperated by comma: Default is {all_queues}",
        )
        parser.add_argument(
            "--celery-args",
            help="All the argument after this are passed to celery",
            nargs=argparse.REMAINDER,
            default=None,
        )
        parser.add_argument(
            "--concurrency",
            type=int,
            default=4,
            help=("Number of Celery worker processes. Defaults to 4 to avoid OOMKilled."),
        )

    def handle(self, *_, **options):
        queues = options["queues"]
        concurrency = options["concurrency"]
        celery_args = options["celery_args"]

        cmd = get_celery_cmd(
            queues=queues,
            concurrency=concurrency,
            celery_args=celery_args,
        )

        self.stdout.write(f"Starting celery worker... {cmd}")
        subprocess.call(shlex.split(cmd))
