import csv
import pytz
from dateutil import parser as date_parser

from django.db import transaction
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point

from api.models import Country
from ...models import DelegationOffice, DelegationOfficeType
from main.managers import BulkCreateManager


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
            bulk_mgr = BulkCreateManager(chunk_size=1000)

            # Prefetch dataset
            country_iso3_id_map = {
                iso3.lower(): _id
                for _id, iso3 in Country.objects.filter(iso3__isnull=False).values_list('id', 'iso3')
            }
            dotype_id_map = {
                name: _id
                for _id, name in DelegationOfficeType.objects.values_list('id', 'name')
            }
            for i, row in enumerate(reader):
                # Without positions we can't use the row:
                if not row['longitude'] or not row['latitude']:
                    continue
                if len(row['postcode']) > 20:
                    print('Not using too long ' + row['postcode'])
                    row['postcode'] = ''  # Better then inserting wrong textual data. Please do not use postal_code.

                dotype = dotype_id_map[row['type']]
                country = country_iso3_id_map[row['iso3'].lower()]
                # We do not check COUNTRY or NATIONAL_SOCIETY, but only this ^

                visibility = 4  # row['visibility']  # 4: IFRC_NS
                is_ns_same_location = row['ns_same_location'].lower() == 'yes'
                is_multiple_ifrc_offices = row['multiple_ifrc_offices'].lower() == 'yes'

                name = row['name']
                city = row['city']
                address = row['address']
                postcode = row['postcode']
                location = Point(float(row['longitude']), float(row['latitude']))
                society_url = row['society_url']
                url_ifrc = row['url_ifrc']
                hod_first_name = row['hod_first_name']
                hod_last_name = row['hod_last_name']
                hod_mobile_number = row['hod_mobile_number']
                hod_email = row['hod_email']
                assistant_name = row['assistant_name']
                assistant_email = row['assistant_email']
                date_of_data = None
                if 'date_of_data' in row and row['date_of_data']:
                    date_of_data = date_parser.parse(row['date_of_data']).replace(tzinfo=pytz.utc)
                do = DelegationOffice(
                    dotype_id=dotype,
                    country_id=country,
                    visibility=visibility,
                    is_ns_same_location=is_ns_same_location,
                    is_multiple_ifrc_offices=is_multiple_ifrc_offices,
                    name=name,
                    city=city,
                    address=address,
                    postcode=postcode,
                    location=location,
                    society_url=society_url,
                    url_ifrc=url_ifrc,
                    hod_first_name=hod_first_name,
                    hod_last_name=hod_last_name,
                    hod_mobile_number=hod_mobile_number,
                    hod_email=hod_email,
                    assistant_name=assistant_name,
                    assistant_email=assistant_email,
                    date_of_data=date_of_data
                )
                bulk_mgr.add(do)
        bulk_mgr.done()
        print('Bulk create summary:', bulk_mgr.summary())
