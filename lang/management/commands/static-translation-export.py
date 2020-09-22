import csv
import polib
from pathlib import Path
from collections import defaultdict
from django.conf import settings
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Export django po files to csv'

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=Path)

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        default_language = settings.LANGUAGE_CODE

        # Collect all data from po
        translation_data = defaultdict(lambda: defaultdict(dict))
        for file in Path('').glob(f"**/{default_language}/**/*.po"):
            path_pattern = str(file).replace(f'/{default_language}/', '/{language}/')
            for lang, _ in settings.LANGUAGES:
                po = polib.pofile(path_pattern.format(language=lang))
                for s in po:
                    translation_data[path_pattern][s.msgid][lang] = s.msgstr

        # Write to csv
        headers = ['file', 'msgid'] + [lang for lang, _ in settings.LANGUAGES]
        with open(csv_file_path, 'w') as fp:
            writer = csv.DictWriter(fp, fieldnames=headers, delimiter=',', lineterminator='\n')
            writer.writeheader()
            for path_pattern, msgid_data in translation_data.items():
                for msgid, values in msgid_data.items():
                    writer.writerow({
                        'file': path_pattern,
                        'msgid': msgid,
                        **{
                            lang: values[lang]
                            for lang, _ in settings.LANGUAGES
                        },
                    })
