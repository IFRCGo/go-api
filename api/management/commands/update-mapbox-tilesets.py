import subprocess
import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

class Command(BaseCommand):
  help = "This command produces a countries.geojson and districts.geojson, and uploads them to Mapbox. It is the source for all GO Maps."

  def handle(self, *args, **options):
    try:
      db = settings.DATABASES[0]
      DB_HOST = db.HOST
      DB_NAME = db.NAME
      DB_USER = db.USER
      DB_PASSWORD = db.PASSWORD
      DB_PORT = db.PORT
      connection_string = 'PG:host={} dbname={} user={} password={} port={}'.format(DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT)

      print('Exporting countries...')
      subprocess.Popen(['rm', '/tmp/countries.geojson'])
      subprocess.Popen(['ogr2ogr', '-f', 'GeoJSON', '/tmp/countries.geojson', connection_string, '-sql', 'select cd.country_id, cd.geom, c.name, c.name_es, c.name_fr, c.name_ar, c.iso, c.region_id, c.iso3, c.independent, c.is_deprecated, c.fdrs, c.record_type from api_countrygeoms cd, api_country c where cd.country_id = c.id and c.record_type=1' ])
      print('Countries written to /tmp/countries.geojson')

      print('Exporting districts...')
      subprocess.Popen(['rm', '/tmp/districts.geojson'])
      subprocess.Popen(['ogr2ogr', '-f', 'GeoJSON', '/tmp/districts.geojson', connection_string, '-sql', 'select cd.district_id, cd.geom, c.name, c.country_id, c.is_enclave, c.is_deprecated from api_districtgeoms cd, api_district c where cd.district_id = c.id and cd.geom is not null' ])
      print('Districts written to /tmp/districts.geojson')

      print('Update Mapbox tileset source for countries...')
      subprocess.Popen(['tilesets', 'upload-source', '--replace', 'go-ifrc', 'go-countries-src', '/tmp/countries.geojson'])

      print('Update Mapbox tileset for countries...')
      subprocess.Popen(['tilesets', 'publish', 'go-ifrc.go-countries'])


      print('Update Mapbox tileset source for districts...')
      subprocess.Popen(['tilesets', 'upload-source', '--replace', 'go-ifrc', 'go-districts-src', '/tmp/districts.geojson'])

      print('Update Mapbox tileset for districts...')
      subprocess.Popen(['tilesets', 'publish', 'go-ifrc.go-districts'])
    except BaseException as e:
      raise CommandError('Could not update tilesets: %s', str(e))