# https://github.com/leepa/django_amazon_translate
import re
from pathlib import Path

import polib
from lagn.translate import AmazonTranslate
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

    def handle(self, *args, **options):
        # Loop through all locale paths defined in the project
        for file in Path('').glob('**/*.po'):
            # NOTE: Make sure this is the right way to get the language
            language = str(file).split('/')[-3]
            print(f'Translating: {file} ({language})')
            po = polib.pofile(file)
            po = translate_po_file(po, language)
            po.save(file)
