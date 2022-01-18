import csv
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import transaction
from api.models import Country

class Command(BaseCommand):
  help = "update the sovereign country and disputed status for all the countries from a CSV file. To run, python manage.py update-sovereign-and-disputed file.csv"
  missing_args_message = "Filename is missing. A CSV file is required."

  def add_arguments(self, parser):
    parser.add_argument('filename', nargs='+', type=str)

  @transaction.atomic
  def handle(self, *args, **options):
    filename = options['filename'][0]
    input_csv = csv.DictReader((open(filename, 'r')), fieldnames=['id', 'iso', 'name', 'sovereign_state', 'disputed'])
    next(input_csv)

    input_by_name = {}
    input_by_id = {}
    for row in input_csv:
      input_by_name[row['name']] = row
      if (row['id']):
        input_by_id[row['id']] = row

    for country_name in input_by_name.keys():
      name = input_by_name[country_name]['name']
      sovereign_state_id = input_by_name[country_name]['sovereign_state']
      disputed = input_by_name[country_name]['disputed']

      if (sovereign_state_id):
        # find this country using the name
        try:
          this_country = Country.objects.get(name=name, record_type=1)
          print(name)
          # find the sovereign state
          sovereign_state = input_by_id[sovereign_state_id]
          if (sovereign_state):
            sovereign_state_iso = sovereign_state['iso']
            sovereign_state_name = sovereign_state['name']
            # find the sovereign state country and map the id
            if (sovereign_state_iso):
              # if iso exists use that.
              sovereign_state_country = Country.objects.get(iso=sovereign_state_iso, record_type=1)
              this_country.sovereign_state = sovereign_state_country
            else:
              # otherwise use name.
              sovereign_state_country = Country.objects.get(name=sovereign_state_name, record_type=1)
              this_country.sovereign_state = sovereign_state_country

          if (disputed):
            this_country.disputed = True

          this_country.save()

        except ObjectDoesNotExist:
          print('Country not found. Make sure names match', name)


