import csv
from datetime import datetime

from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.db import transaction


from api.models import Country
from ...models import LocalUnit, LocalUnitType
from main.managers import BulkCreateManager


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
            bulk_mgr = BulkCreateManager(chunk_size=1000)
            # Prefetch
            country_name_id_map = {
                country_name.lower(): _id
                for _id, country_name in Country.objects.values_list('id', 'name')
            }
            local_unit_id_map = {
                code: _id
                for _id, code in LocalUnitType.objects.values_list('id', 'code')
            }

            for i, row in enumerate(reader, start=2):
                # Without positions we can't use the row:
                if not row['LONGITUDE'] or not row['LATITUDE']:
                    self.stdout.write(
                        self.style.WARNING(f'Skipping row {i}: Empty locations point')
                    )
                    continue

                country = country_name_id_map[row['COUNTRY'].lower()]
                type = local_unit_id_map[int(row['TYPE CODE'])]
                visibility = 3 if row['VISIBILITY'].lower() == 'public' else 1
                health_id = row['DATA SOURCE ID']
                if not health_id.isdigit():
                    health_id = None
                validated = True
                local_branch_name = row['NAME_LOC']
                address_loc = row['ADDRESS_LOC']
                focal_person_loc = row['FOCAL_PERSON_LOC']
                location = Point(float(row['LONGITUDE']), float(row['LATITUDE']))
                date_of_data = None
                if row['DATE OF UPDATE']:
                    date_of_data = datetime.strptime(row['DATE OF UPDATE'], '%Y-%m-%d').strftime("%Y-%m-%d")  # sometimes it was in '%m/%d/%Y
                local_unit = LocalUnit(
                    country_id=country,
                    type_id=type,
                    visibility=visibility,
                    validated=validated,
                    local_branch_name=local_branch_name,
                    address_loc=address_loc,
                    focal_person_loc=focal_person_loc,
                    location=location,
                    date_of_data=date_of_data,
                    health_id=health_id
                )
                bulk_mgr.add(local_unit)
            bulk_mgr.done()
            print('Bulk create summary:', bulk_mgr.summary())
