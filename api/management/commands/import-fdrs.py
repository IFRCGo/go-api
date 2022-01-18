import csv
from django.core.management.base import BaseCommand, CommandError
from api.models import Country
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

class Command(BaseCommand):
  help = "import fdrs code for countries based on iso2. To run, python manage.py import-fdrs iso-fdrs.csv"

  def add_arguments(self, parser):
    parser.add_argument('filename', nargs='+', type=str)
  
  @transaction.atomic
  def handle(self, *args, **options):
    filename = options['filename'][0]
    input_file = csv.DictReader(open(filename, 'r'), fieldnames=['iso', 'fdrs'])
    next(input_file)
    for row in input_file:
      iso = row['iso'].lower()
      fdrs = row['fdrs']
      try:
        country = Country.objects.get(iso=iso, record_type=1)
        country.fdrs = fdrs
        country.save()
      except ObjectDoesNotExist:
        print('country does not exist', iso)
    print('done!')