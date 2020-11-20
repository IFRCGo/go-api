import subprocess
import os
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
  help = "This command produces a countries.geojson and districts.geojson to be uploaded to Mapbox as a tileset. It is the source for all GO Maps."

  def handle(self, *args, **options):
    try:
      DB_HOST = os.environ['DJANGO_DB_HOST']
      DB_NAME = os.environ['DJANGO_DB_NAME']
      DB_USER = os.environ['DJANGO_DB_USER']
      DB_PASSWORD = os.environ['DJANGO_DB_PASS']
      connection_string = 'PG:host={} dbname={} user={} password={}'.format(DB_HOST, DB_NAME, DB_USER, DB_PASSWORD)

      print('Exporting countries...')
      subprocess.Popen(['rm', '/tmp/countries.geojson'])
      subprocess.Popen(['ogr2ogr', '-f', 'GeoJSON', '/tmp/countries.geojson', connection_string, '-sql', 'select cd.country_id, cd.geom, c.name, c.iso, c.region_id, c.iso3, c.independent, c.is_deprecated, c.fdrs, c.record_type from api_countrygeoms cd, api_country c where cd.country_id = c.id and c.record_type=1' ])
      print('Countries written to /tmp/countries.geojson')

      print('Exporting districts...')
      subprocess.Popen(['rm', '/tmp/districts.geojson'])
      subprocess.Popen(['ogr2ogr', '-f', 'GeoJSON', '/tmp/districts.geojson', connection_string, '-sql', 'select cd.district_id, cd.geom, c.name, c.country_id, c.is_enclave, c.is_deprecated from api_districtgeoms cd, api_district c where cd.district_id = c.id' ])
      print('Districts written to /tmp/districts.geojson')

    except:
      raise CommandError('Could not generate geojson')