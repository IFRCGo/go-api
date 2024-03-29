from django.db import transaction
import csv
import pytz
from dateutil import parser as date_parser
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point


from api.models import Country
from ...models import LocalUnit, LocalUnitType


class Command(BaseCommand):
    help = "Import LocalUnits data from CSV"
    missing_args_message = "Filename is missing. Filename / path to CSV file required. Required headers in CSV: distr_code, GOadm2code, ADM2"

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs='+', type=str)

    @transaction.atomic
    def handle(self, *args, **options):
        filename = options['filename'][0]
        with open(filename) as csvfile:
            reader = csv.DictReader(csvfile)
            for i, row in enumerate(reader):
                # Without positions we can't use the row:
                if not row['LONGITUDE'] or not row['LATITUDE']:
                    continue
                unit = LocalUnit()
                unit.country = Country.objects.get(name=row['COUNTRY'])
                unit.type = LocalUnitType.objects.get(
                    code=row['TYPE CODE'],
                )
                unit.is_public = row['VISIBILITY'].lower() == 'public'
                unit.validated = True
                unit.local_branch_name = row['NAME_LOC']
                unit.address_loc = row['ADDRESS_LOC']
                unit.focal_person_loc = row['FOCAL_PERSON_LOC']
                unit.location = Point(float(row['LONGITUDE']), float(row['LATITUDE']))
                if row['DATE OF UPDATE']:
                    unit.date_of_data = date_parser.parse(row['DATE OF UPDATE']).replace(tzinfo=pytz.utc)
                unit.save()
                name = unit.local_branch_name if unit.local_branch_name else unit.english_branch_name
                if name:
                    print(f'{i} | {name} saved')
                else:
                    print(f'{i} | *** entity with ID saved')
