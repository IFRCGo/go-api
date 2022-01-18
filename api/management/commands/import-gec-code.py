import csv
from django.core.management.base import BaseCommand, CommandError
from api.models import Country, GECCode
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

class Command(BaseCommand):
  help = "import a CSV file with GEC and country iso code to the GECCode model. To run, python manage.py import-gec-code codes.csv"
  missing_args_message = "Filename is missing. A valid CSV file is required."

  def add_arguments(self, parser):
    parser.add_argument('filename', nargs='+', type=str)

  @transaction.atomic
  def handle(self, *Args, **options):
    filename = options['filename'][0]
    gec_file = csv.DictReader(open(filename, 'r'), fieldnames=['GST_code', 'GST_name', 'GO ID', 'ISO'])
    next(gec_file)
    for row in gec_file:
      iso = row['ISO']
      code = row['GST_code']
      try:
        country = Country.objects.get(iso=iso, record_type=1)
        gec = GECCode()
        gec.code = code
        gec.country = country
        gec.save()
        print('Done!')
      except ObjectDoesNotExist:
        print('missing country', iso)
      except MultipleObjectsReturned:
        print('more than one country with that iso', iso)