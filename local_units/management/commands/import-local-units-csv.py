import csv
from datetime import datetime

from django.db import transaction
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point


from api.models import Country
from ...models import LocalUnit, LocalUnitType, LocalUnitLevel
from main.managers import BulkCreateManager


class Command(BaseCommand):
    help = "Import LocalUnits data from CSV"
    missing_args_message = "Filename is missing. Filename / path to CSV file required. Required headers in CSV: distr_code, GOadm2code, ADM2"

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs='+', type=str)

    def parse_date(self, date):
        if not date:
            return

        possible_date_format = ('%d-%b-%y', '%m/%d/%Y')
        for date_format in possible_date_format:
            try:
                return datetime.strptime(date, date_format).strftime("%Y-%m-%d")
            except ValueError:
                pass

    @transaction.atomic
    def handle(self, *args, **options):
        filename = options['filename'][0]
        with open(filename) as csvfile:
            reader = csv.DictReader(csvfile)
            bulk_mgr = BulkCreateManager(chunk_size=1000)

            # Prefetch dataset
            country_iso3_id_map = {
                iso3.lower(): _id
                for _id, iso3 in Country.objects.filter(iso3__isnull=False).values_list('id', 'iso3')
            }
            local_unit_id_map = {
                code: _id
                for _id, code in LocalUnitType.objects.values_list('id', 'code')
            }
            local_unit_level_id_map = {
                level: _id
                for _id, level in LocalUnitLevel.objects.values_list('id', 'level')
            }

            for i, row in enumerate(reader):
                # Without positions we can't use the row:
                if not row['LONGITUDE'] or not row['LATITUDE']:
                    self.stdout.write(
                        self.style.WARNING(f'Skipping row {i}: Empty locations point')
                    )
                    continue
                if len(row['POSTCODE']) > 10:
                    row['POSTCODE'] = ''  # better then inserting wrong textual data
                country = country_iso3_id_map[row['ISO3'].lower()]
                # We do not check COUNTRY or NATIONAL_SOCIETY, but only this ^
                row['TYPECODE'] = {
                    'NS0': 1,
                    'NS1': 2,
                    'NS2': 3,
                    'NS3': 4,
                }.get(
                    row['TYPECODE'],
                    int(row['TYPECODE']),
                )
                _type = local_unit_id_map[int(row['TYPECODE'])]
                level = None
                if row['LEVELCODE']:
                    level = local_unit_level_id_map[int(row['LEVELCODE'])]
                subtype = row['SUBTYPE']
                is_public = row['PUBLICVIEW'].lower() == 'yes'
                validated = row['VALIDATED'].lower() == 'yes'
                local_branch_name = row['NAME_LOC']
                english_branch_name = row['NAME_EN']
                postcode = row['POSTCODE'].strip()[:10]
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
                date_of_data = self.parse_date(row['DATEOFUPDATE'])
                local_unit = LocalUnit(
                    country_id=country,
                    type_id=_type,
                    level_id=level,
                    subtype=subtype,
                    # is_public=is_public,
                    validated=validated,
                    local_branch_name=local_branch_name,
                    english_branch_name=english_branch_name,
                    postcode=postcode,
                    address_en=address_en,
                    address_loc=address_loc,
                    city_en=city_en,
                    city_loc=city_loc,
                    focal_person_en=focal_person_en,
                    focal_person_loc=focal_person_loc,
                    phone=phone,
                    email=email,
                    link=link,
                    source_en=source_en,
                    source_loc=source_loc,
                    location=location,
                    date_of_data=date_of_data,
                )
                bulk_mgr.add(local_unit)
        bulk_mgr.done()
        print('Bulk create summary:', bulk_mgr.summary())
