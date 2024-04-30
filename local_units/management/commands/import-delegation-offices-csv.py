from django.db import transaction
import csv
import pytz
from dateutil import parser as date_parser
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import Point


from api.models import Country
from ...models import DelegationOffice, DelegationOfficeType


# Don't use the received header's always changing upperlowercase header, use a row like this:
# name type    city    address postcode latitude    longitude   iso iso3    country ifrc_region_number  ifrc_region_name    society_name    society_url url_ifrc    ns_same_location    multiple_ifrc_offices   office_tier hod_first_name  hod_last_name   hod_mobile_number   hod_email   assistant_name  assistant_email


class Command(BaseCommand):
    help = "Import DelegationOffices data from CSV"
    missing_args_message = "Filename is missing. Filename / path to CSV file required."

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs='+', type=str)

    @transaction.atomic
    def handle(self, *args, **options):
        filename = options['filename'][0]
        with open(filename) as csvfile:
            reader = csv.DictReader(csvfile, delimiter='\t')
            for i, row in enumerate(reader):
                # Without positions we can't use the row:
                if not row['longitude'] or not row['latitude']:
                    continue
                if len(row['postcode']) > 20:
                    print('Not using too long ' + row['postcode'])
                    row['postcode'] = ''  # Better then inserting wrong textual data. Please do not use postal_code.
                do = DelegationOffice()

                do.dotype = DelegationOfficeType.objects.get(name=row['type'])
                do.country = Country.objects.get(iso3=row['iso3'])
                # We do not check COUNTRY or NATIONAL_SOCIETY, but only this ^

                do.visibility = 4  # row['visibility']  # 4: IFRC_NS
                do.is_ns_same_location = row['ns_same_location'].lower() == 'yes'
                do.is_multiple_ifrc_offices = row['multiple_ifrc_offices'].lower() == 'yes'

                do.name = row['name']
                do.city = row['city']
                do.address = row['address']
                do.postcode = row['postcode']
                do.location = Point(float(row['longitude']), float(row['latitude']))
                do.society_url = row['society_url']
                do.url_ifrc = row['url_ifrc']
                do.hod_first_name = row['hod_first_name']
                do.hod_last_name = row['hod_last_name']
                do.hod_mobile_number = row['hod_mobile_number']
                do.hod_email = row['hod_email']
                do.assistant_name = row['assistant_name']
                do.assistant_email = row['assistant_email']
                if 'date_of_data' in row and row['date_of_data']:
                    do.date_of_data = date_parser.parse(row['date_of_data']).replace(tzinfo=pytz.utc)
                do.save()
                if do.name:
                    print(f'{i} | {do.name} saved')
                else:
                    print(f'{i} | *** entity with ID saved')
