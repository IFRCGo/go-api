import csv
from datetime import datetime

from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.db import transaction


from api.models import Country
from local_units.models import LocalUnit, LocalUnitType
from main.managers import BulkCreateManager


class Command(BaseCommand):
    help = "Import LocalUnits data from CSV"
    missing_args_message = "Filename is missing. Filename / path to CSV file required. Required headers in CSV: distr_code, GOadm2code, ADM2"

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs='+', type=str)

    @transaction.atomic
    def handle(self, *args, **options):

        def parse_date(date):
            today = datetime.today()
            if not date:
                return today.strftime("%Y-%m-%d")
                # date_of_data is a non-nullable field, so we need at least this ^

            possible_date_format = ('%d-%b-%y', '%m/%d/%Y', '%Y-%m-%d')
            for date_format in possible_date_format:
                try:
                    return datetime.strptime(date, date_format).strftime("%Y-%m-%d")
                except ValueError:
                    return today.strftime("%Y-%m-%d")

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
                if not row['NAME_LOC'] or not ['NAME_EN']:
                    self.stdout.write(
                        self.style.WARNING(f'Skipping row {i}: Empty brach name combination')
                    )
                    continue

                country = country_name_id_map[row['COUNTRY'].lower()]
                type = local_unit_id_map[int(row['TYPE CODE'])]
                subtype = row['SUBTYPE']  # FIXME just a text field
                visibility = 3 if row['VISIBILITY'].lower() == 'public' else 1
                health_id = row['DATA SOURCE ID']
                if not health_id.isdigit():
                    health_id = None
                validated = True
                level_id = int(row['COVERAGECODE']) + 1
                local_branch_name = row['NAME_LOC']
                english_branch_name = row['NAME_EN']
                postcode = row['POSTCODE']
                address_loc = row['ADDRESS_LOC']
                address_en = row['ADDRESS_EN']
                city_loc = row['CITY_LOC']
                city_en = row['CITY_EN']
                focal_person_loc = row['FOCAL_PERSON_LOC']
                focal_person_en = row['FOCAL_PERSON_EN']
                phone = row['TELEPHONE'].strip()[:30]
                email = row['EMAIL']
                link = row['WEBSITE']
                source_en = row['SOURCE_EN']
                source_loc = row['SOURCE_LOC']
                location = Point(float(row['LONGITUDE']), float(row['LATITUDE']))
                visibility = 3 if row['VISIBILITY'].lower() == 'public' else 1
                date_of_data = parse_date(row['DATE OF UPDATE'])
                local_unit = LocalUnit(
                    level_id=level_id,
                    country_id=country,
                    type_id=type,
                    # is_public=is_public,
                    validated=validated,
                    local_branch_name=local_branch_name,
                    english_branch_name=english_branch_name,
                    focal_person_loc=focal_person_loc,
                    focal_person_en=focal_person_en,
                    location=location,
                    postcode=postcode,
                    address_loc=address_loc,
                    address_en=address_en,
                    city_loc=city_loc,
                    city_en=city_en,
                    phone=phone,
                    email=email,
                    link=link,
                    source_loc=source_loc,
                    source_en=source_en,
                    date_of_data=date_of_data,
                    health_id=health_id,
                    visibility=visibility,
                    subtype=subtype,
                )
                bulk_mgr.add(local_unit)
            bulk_mgr.done()
            print('Bulk create summary:', bulk_mgr.summary())
