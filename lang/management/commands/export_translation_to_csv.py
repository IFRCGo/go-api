import csv
import polib
from pathlib import Path
from django.conf import settings
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Export django po files to xlsx'

    def handle(self, *args, **options):
        default_language = settings.LANGUAGE_CODE
        headers = ['file', 'msgid'] + [lang[0] for lang in settings.LANGUAGES]
        writer = csv.DictWriter(self.stdout, fieldnames=headers, lineterminator='\n')
        writer.writeheader()
        for file in Path('').glob(f"**/{default_language}/**/*.po"):
            po = polib.pofile(file)
            for s in po:
                writer.writerow({
                    'file': file,
                    'msgid': s.msgid,
                    default_language: s.msgstr,
                })
