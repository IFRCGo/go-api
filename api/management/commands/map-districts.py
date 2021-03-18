import csv
from django.core.management.base import BaseCommand
from api.models import Country, District
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned


class Command(BaseCommand):
    help = 'Maps some orphan districts to countries. join_districts_to_country.csv is required (Johnny)'
    missing_args_message = "Filename is missing. A valid CSV file is required."

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs='+', type=str)

    @transaction.atomic
    def handle(self, *args, **options):
        filename = options['filename'][0]
        rows = csv.DictReader(open(filename, 'r'), fieldnames=['District code', 'Country ISO'])
        next(rows)
        for row in rows:
            dcode = row['District code']
            iso = row['Country ISO']
            try:
                country = Country.objects.get(iso=iso, record_type=1)
                district = District.objects.get(code=dcode)
                district.country = country
                district.country_name = country.name
                district.country_iso = country.iso
                district.save()
            except ObjectDoesNotExist:
                print(f'Missing Country ({iso}) or District ({dcode})')
            except MultipleObjectsReturned:
                print(f'More than one Country with ({iso}) or District with ({dcode})')
        print('Done!')
