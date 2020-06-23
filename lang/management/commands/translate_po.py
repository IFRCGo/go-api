# https://github.com/leepa/django_amazon_translate
import re
from pathlib import Path

import polib
from lang.translation import AmazonTranslate, DJANGO_AVAILABLE_LANGUAGES
from django.core.management import BaseCommand


def translate_po_file(po, language):
    """
    Update a given .po file with translated strings from Amazon Translate.
    """
    # Get a client for translations
    translate = AmazonTranslate()
    for s in po.untranslated_entries():
        # We replace the formatting specifiers with something
        # that Amazon Translate will just assume is a title and
        # not translate.
        subbed_message = re.sub(
            r"%\((\w+)\)s", r"FORMAT_\1_END", s.msgid
        )
        # Translate the text itself
        response = translate.translate_text(
            subbed_message,
            "en",
            language,
        )
        # Put back the correct gettext formatting
        s.msgstr = re.sub(
            r"FORMAT_(\w+)_END", r"%(\1)s",
            response['TranslatedText']
        )
    return po


class Command(BaseCommand):
    help = 'Use Amazon Translate to translate all the .po files, Already translated strings are not touched'

    def add_arguments(self, parser):
        parser.add_argument(
            '--languages', nargs='+',
            choices=DJANGO_AVAILABLE_LANGUAGES,
            help='Languages to translate. Default is all',
        )

    def handle(self, *args, **options):
        languages = options['languages'] or DJANGO_AVAILABLE_LANGUAGES
        for language in languages:
            for file in Path('').glob(f"**/{language}/**/*.po"):
                print(f'Translating: {file} ({language})')
                po = polib.pofile(file)
                po = translate_po_file(po, language)
                po.save(file)
