from django.db import transaction
import csv
from django.core.management.base import BaseCommand, CommandError
from api.models import Country, District


def get_bool(value):
    if value == 't':
        return True
    elif value == 'f':
        return False
    else:
        return None

def get_int(value):
    # print('GET INT', value)
    if value == '':
        return None
    else:
        return int(float(value))


class Command(BaseCommand):
    help = "Import countries data from CSV (only to be used on staging)"
    missing_args_message = "Filename is missing. Filename / path to CSV file required."

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs='+', type=str)

    @transaction.atomic
    def handle(self, *args, **options):
        filename = options['filename'][0]
        boolean_fields = ['is_deprecated', 'is_enclave']
        int_fields = ['country_id', 'wp_population', 'wb_year']
        fields_to_save = [
            'name',
            'code',
            'country_iso',
            'country_name',
            'bbox',
            'centroid'
        ] + boolean_fields + int_fields
        with open(filename) as csvfile:
            all_ids = []
            reader = csv.DictReader(csvfile)
            failures = 0
            for row in reader:
                id = int(row.pop('id'))
                all_ids.append(id)
                try:
                    district = District.objects.get(pk=id)
                except:
                    district = District()
                for key in row.keys():
                    # print(key)
                    if key in boolean_fields:
                        val = get_bool(row[key])
                    elif key in int_fields:
                        val = get_int(row[key])
                    else:
                        val = row[key]
                    if key in fields_to_save:  
                        district.__setattr__(key, val)
                try:
                    district.save()
                    print('SUCCESS', district.name)
                except:
                    print('FAILED', district.name)
                    failures += 1
        print('done importing districts, with %d failures' % failures)
        existing_district_ids = [d.id for d in District.objects.all()]
        districts_not_in_csv = list(set(existing_district_ids) - set(all_ids))
        for district_id in districts_not_in_csv:
            d = District.objects.get(pk=district_id)
            d.delete()
        print('deleted ids', districts_not_in_csv)