import csv

from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import District, Admin2


class Command(BaseCommand):
    help = "Import admin2 data from CSV"
    missing_args_message = (
        "Filename is missing. Filename / path to CSV file required. Required headers in CSV: distr_code, GOadm2code, ADM2"
    )

    def add_arguments(self, parser):
        parser.add_argument("filename", nargs="+", type=str)

    @transaction.atomic
    def handle(self, *args, **options):
        filename = options["filename"][0]
        with open(filename) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                district_code = row["distr_code"]
                district = District.objects.get(code=district_code)
                adm2_code = row["GOadm2code"]
                try:
                    adm2 = Admin2.objects.get(code=adm2_code)
                except:
                    adm2 = Admin2()
                adm2.code = adm2_code
                adm2.admin1 = district
                adm2.name = row["ADM2"]
                adm2.save()
                print(f"{adm2.name} saved")
