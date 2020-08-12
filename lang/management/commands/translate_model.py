import logging
from django.core.management import BaseCommand

from lang.tasks import ModelTranslator


class Command(BaseCommand):
    help = 'Use Amazon Translate to translate all models translated field\'s values'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size', metavar='N', type=int, default=None,
            help='how many instances to translate for each model'
        )

        parser.add_argument(
            '--show-counts-only',
            action='store_true',
            help='Show characters counts only',
        )

    def handle(self, *args, **options):
        logging.getLogger('').setLevel(logging.INFO)
        if options.get('show_counts_only'):
            ModelTranslator.show_characters_counts()
        else:
            ModelTranslator().run(batch_size=options.pop('batch_size') or 100)
