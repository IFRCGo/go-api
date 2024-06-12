import csv
import hashlib
from argparse import FileType
from collections import defaultdict
from sys import stdout

from django.core.management import BaseCommand
from django.db import transaction

from lang.models import String


def get_md5_hash(value):
    hash_md5 = hashlib.md5()
    hash_md5.update(value.encode("UTF-8"))
    return hash_md5.hexdigest()


class Command(BaseCommand):
    help = "Export client translation data to csv"

    def add_arguments(self, parser):
        parser.add_argument("output_file", nargs="?", type=FileType("w"), default=stdout)

    @transaction.atomic
    def handle(self, *_, **options):
        output_file = options["output_file"]
        # Collect all data from csv
        csv_writer = csv.DictWriter(
            output_file,
            fieldnames=(
                "page_name",
                "key",
                "value",
                "es",
                "fr",
                "ar",
            ),
        )

        string_qs = String.objects.all()
        string_data = defaultdict(dict)
        """
        key: {
            key: key,
            page_name: page_name,
            value: en-value,
            es: es-value
            fr: fr-value
            ar: ar-value
        """

        self.stdout.write(f"Total String: {string_qs.count()}")
        csv_writer.writeheader()
        for string in string_qs:
            code = f"{string.page_name}-{string.key}"
            if string.language == "en":
                string_data[code]["key"] = string.key
                string_data[code]["page_name"] = string.page_name
                string_data[code]["value"] = string.value
            else:
                string_data[code][string.language] = string.value
        for string_datum in string_data.values():
            csv_writer.writerow(string_datum)
