from django.db import transaction
import csv
from django.core.management.base import BaseCommand, CommandError
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
            for row in reader:
                unit = LocalUnit()
                unit.country = Country.objects.get(iso3=row['ISO3'])
                unit.type = LocalUnitType.objects.get_or_create(
                    level=row['TYPECODE'],
                    name=row['TYPENAME']
                )[0]
                unit.name_loc = row['NAME_LOC']
                unit.name_en = row['NAME_EN']
                unit.branch_level = int(row['TYPECODE'])
                unit.postcode = int(row['POSTCODE']) if row['POSTCODE'] else None
                unit.address_loc = row['ADDRESS_LOC']
                unit.address_en = row['ADDRESS_EN']
                unit.city_loc = row['CITY_LOC']
                unit.city_en = row['CITY_EN']
                unit.focal_person_loc = row['FOCAL_PERSON_LOC']
                unit.focal_person_en = row['FOCAL_PERSON_EN']
                unit.phone = row['TELEPHONE']
                unit.email = row['EMAIL']
                unit.link = row['WEBSITE']
                unit.source_en = row['SOURCE_EN']
                unit.source_loc = row['SOURCE_LOC']
                unit.location = Point(float(row['LONGITUDE']), float(row['LATITUDE']))
                unit.save()
                print(f'{unit.name_en} saved')
