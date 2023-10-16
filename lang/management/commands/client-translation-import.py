import csv
import hashlib
from sys import stdin
from argparse import FileType
from django.core.management import BaseCommand
from django.db import transaction

from lang.models import String


def get_md5_hash(value):
    hash_md5 = hashlib.md5()
    hash_md5.update(value.encode('UTF-8'))
    return hash_md5.hexdigest()


class Command(BaseCommand):
    help = 'Import from csv and update client translation data. lang.models.py:String'

    def add_arguments(self, parser):
        parser.add_argument('input_file', nargs='?', type=FileType('r'), default=stdin)

    @transaction.atomic
    def handle(self, *_, **options):
        input_file = options['input_file']
        if input_file.isatty():
            self.stderr.write(
                self.style.ERROR('Empty file'),
            )
            return

        # Collect all data from csv
        reader = csv.DictReader(input_file)
        updated = 0
        for row in reader:
            string_key = row['key']
            if string_key is None:
                continue
            page_name = row['namespace']
            string_value_en = row['value']
            string_value_hash = get_md5_hash(string_value_en)
            self.stdout.write(f'Saving {string_key}')
            for lang, _ in String.language.field.choices:
                client_string, _ = String.objects.get_or_create(
                    key=string_key,
                    language=lang,
                )
                if lang == 'en':
                    client_string.value = string_value_en
                else:
                    client_string.value = row[lang]
                client_string.page_name = page_name
                client_string.hash = string_value_hash
                client_string.save()
            updated += 1
        self.stdout.write(
            self.style.SUCCESS(f'Saved {updated} strings'),
        )
