import logging
from django.core.management import BaseCommand

from lang.tasks import TranslateModel


class Command(BaseCommand):
    help = 'Use Amazon Translate to translate all models translated field\'s values'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size', metavar='N', type=int, default=None,
            help='how many instances to translate for each model'
        )

    def handle(self, *args, **options):
        logging.getLogger('').setLevel(logging.INFO)
        TranslateModel().run(batch_size=options.pop('batch_size'))
