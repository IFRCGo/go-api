import csv
import polib
from pathlib import Path
from collections import defaultdict
from django.conf import settings
from django.core.management import BaseCommand


AVAILABLE_LANGUAGES = [lang for lang, _ in settings.LANGUAGES]


class Command(BaseCommand):
    help = 'Export django po files to csv'

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=Path)
        parser.add_argument(
            '--languages', nargs='+',
            choices=AVAILABLE_LANGUAGES,
            help='Languages to export. Default is all',
        )
        parser.add_argument(
            '--only-new',
            action='store_true',
            help='Only include new(empty) strings'
        )

    def handle(self, *args, **options):
        languages = options['languages'] or AVAILABLE_LANGUAGES
        only_new = options['only_new']
        csv_file_path = options['csv_file']
        default_language = settings.LANGUAGE_CODE

        # Collect all data from po
        translation_data = defaultdict(lambda: defaultdict(lambda: defaultdict(str)))
        for file in Path('').glob(f"**/{default_language}/**/*.po"):
            path_pattern = str(file).replace(f'/{default_language}/', '/{language}/')
            for lang in languages:
                po = polib.pofile(path_pattern.format(language=lang))
                for s in po:
                    translation_data[path_pattern][s.msgid][lang] = s.msgstr
            # If only-new is specified, then strings with atleast one empty string value is added
            if only_new:
                for msgid in list(translation_data[path_pattern].keys()):
                    if all(translation_data[path_pattern][msgid].values()):
                        # Remove data where none are emtpy
                        del translation_data[path_pattern][msgid]

        # Write to csv
        headers = ['file', 'msgid'] + languages
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
                            for lang in languages
                        },
                    })
