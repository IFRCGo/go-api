import csv
import polib
from collections import defaultdict
from pathlib import Path
from django.conf import settings
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Import from csv and update django po files'

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=Path)
        parser.add_argument(
            '--partial-update',
            action='store_true',
            help='Don\'t enforce all languages'
        )

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        partial_update = options['partial_update']

        # Collect all data from csv
        translation_data = defaultdict(lambda: defaultdict(dict))
        with open(csv_file_path) as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                # Default language po file path eg: api/locale/{language}/LC_MESSAGES/django.po
                path_pattern = row['file']
                msgid = row['msgid']
                values = {
                    lang: row[lang]
                    for lang, _ in settings.LANGUAGES
                    if row.get(lang) or not partial_update
                }
                translation_data[path_pattern][msgid] = values

        # Write to po
        for path_pattern, msgid_data in translation_data.items():
            for lang, _ in settings.LANGUAGES:
                file = path_pattern.format(language=lang)
                po = polib.pofile(file)
                for s in po:
                    s.msgstr = msgid_data[s.msgid].get(lang, s.msgstr)
                po.save(file)
