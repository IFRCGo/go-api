import os
from django.db import transaction
import csv
from django.core.management.base import BaseCommand, CommandError
from api.models import Country


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
    missing_args_message = "Filename is missing. Filename / path to CSV file is a required argument."

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs='+', type=str)

    @transaction.atomic
    def handle(self, *args, **options):
        filename = options['filename'][0]
        boolean_fields = ['is_deprecated', 'independent']
        int_fields = ['record_type', 'wp_population', 'wb_year', 'region_id', 'inform_score']
        fields_to_save = [
            'name',
            'name_en',
            'name_es',
            'name_fr',
            'name_ar',
            'iso',
            'society_name',
            'society_name_en',
            'society_name_es',
            'society_name_fr',
            'society_name_ar',
            'society_url',
            'key_priorities',
            'logo',
            'iso3',
            'url_ifrc',
            'geom',
            'centroid',
            'bbox'] + boolean_fields + int_fields
        if not os.path.exists(filename):
            print('File does not exist. Check path?')
            return
        with open(filename) as csvfile:
            all_ids = []
            reader = csv.DictReader(csvfile)
            for row in reader:
                id = int(row.pop('id'))
                all_ids.append(id)
                try:
                    country = Country.objects.get(pk=id)
                except:
                    country = Country()
                for key in row.keys():
                    # print(key)
                    if key in boolean_fields:
                        val = get_bool(row[key])
                    elif key in int_fields:
                        val = get_int(row[key])
                    else:
                        val = row[key]
                    if key in fields_to_save:  
                        country.__setattr__(key, val)
                
                country.save()
                print('SUCCESS', country.name_en)
            print('done importing countries')

        existing_country_ids = [c.id for c in Country.objects.all()]
        countries_not_in_csv = list(set(existing_country_ids) - set(all_ids))
        for country_id in countries_not_in_csv:
            c = Country.objects.get(pk=country_id)
            c.delete()
        print('deleted ids', countries_not_in_csv)