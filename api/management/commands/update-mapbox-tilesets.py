import subprocess
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import time
import os

class Command(BaseCommand):
  help = "This command produces a countries.geojson and districts.geojson, and uploads them to Mapbox. It is the source for all GO Maps."

  missing_args_message = "Argument missing. Specify --update-countries, --update-districts or --update-all."

  def add_arguments(self, parser):
    parser.add_argument(
      '--update-countries',
      action='store_true',
      help='Update tileset for countries'
      )
    parser.add_argument(
      '--update-districts',
      action='store_true',
      help='Update tileset for districts'
      )
    parser.add_argument(
      '--update-all',
      action='store_true',
      help='Update tileset for countries and districts'
    )

  def handle(self, *args, **options):
    try:
      db = settings.DATABASES['default']
      DB_HOST = db['HOST']
      DB_NAME = db['NAME']
      DB_USER = db['USER']
      DB_PASSWORD = db['PASSWORD']
      DB_PORT = 5432
      connection_string = 'PG:host={} dbname={} user={} password={} port={}'.format(DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT)

      if (os.getenv("MAPBOX_ACCESS_TOKEN") is None):
        raise Exception('MAPBOX_ACCESS_TOKEN must be set')

      if options['update_countries'] or options['update_all']:
        self.update_countries(connection_string)

      if options['update_districts'] or options['update_all']:
        self.update_districts(connection_string)

    except BaseException as e:
      raise CommandError('Could not update tilesets: ' + str(e))

  def update_countries(self, connection_string):
    try:
      print('Exporting countries...')
      subprocess.check_call(['touch', '/tmp/countries.geojson'])
      subprocess.check_call(['rm', '/tmp/countries.geojson'])
      subprocess.check_call(['ogr2ogr', '-f', 'GeoJSON', '/tmp/countries.geojson', connection_string, '-sql', 'select cd.country_id, cd.geom, c.name, c.name_es, c.name_fr, c.name_ar, c.iso, c.region_id, c.iso3, c.independent, c.is_deprecated, c.disputed, c.fdrs, c.record_type from api_countrygeoms cd, api_country c where cd.country_id = c.id and c.record_type=1' ])
      print('Countries written to /tmp/countries.geojson')
    except Exception as e:
      print('Failed to export countries', e)
      raise

    try:
      print('Exporting country centroids...')
      subprocess.check_call(['touch', '/tmp/country-centroids.geojson'])
      subprocess.check_call(['rm', '/tmp/country-centroids.geojson'])
      subprocess.check_call(['ogr2ogr', '-lco', 'COORDINATE_PRECISION=4', '-f', 'GeoJSON', '/tmp/country-centroids.geojson', connection_string, '-sql', 'select id as country_id, name_en as name, name_ar, name_es, name_fr, independent, disputed, is_deprecated, iso, iso3, record_type, fdrs, region_id, centroid from api_country where centroid is not null'])
    except Exception as e:
      print('Failed to export country centroids', e)
      raise

    try:
      print('Update Mapbox tileset source for countries...')
      subprocess.check_call(['tilesets', 'upload-source', '--replace', 'go-ifrc', 'go-countries-src', '/tmp/countries.geojson'])
    except Exception as e:
      print('Failed to update tileset source for countries', e)
      raise

    try:
      print('Update Mapbox tileset for countries... and sleeping a minute')
      subprocess.check_call(['tilesets', 'publish', 'go-ifrc.go-countries'])
      time.sleep(60)
    except Exception as e:
      print('Failed to update tileset for countries', e)
      raise

    try:
      print('Update Mapbox tileset source for country centroids...')
      subprocess.check_call(['tilesets', 'upload-source', '--replace', 'go-ifrc', 'go-country-centroids', '/tmp/country-centroids.geojson'])
    except Exception as e:
      print('Failed to update tileset source for country centroids')
      raise

    try:
      print('Update Mapbox tileset for country centroids... and sleeping a minute')
      subprocess.check_call(['tilesets', 'publish', 'go-ifrc.go-country-centroids'])
      time.sleep(60)
    except Exception as e:
      print('Failed to update tileset for country centroids')
      raise


  def update_districts(self, connection_string):
    try:
      print('Exporting districts...')
      subprocess.check_call(['touch', '/tmp/districts.geojson'])
      subprocess.check_call(['rm', '/tmp/districts.geojson'])
      # FIXME eventually should be name_en, name_es etc.
      subprocess.check_call(['ogr2ogr', '-lco', 'COORDINATE_PRECISION=5', '-f', 'GeoJSON', '/tmp/districts.geojson', connection_string, '-sql', 'select cd.district_id, cd.geom, c.name, c.code, c.country_id, c.is_enclave, c.is_deprecated, country.iso as country_iso, country.iso3 as country_iso3, country.name as country_name, country.name_es as country_name_es, country.name_fr as country_name_fr, country.name_ar as country_name_ar from api_districtgeoms cd, api_district c, api_country country where cd.district_id = c.id and cd.geom is not null and country.id=c.country_id' ])
      print('Districts written to /tmp/districts.geojson')
    except Exception as e:
      print('Failed to export districts', e)
      raise

    try:
      print('Exporting district centroids...')
      subprocess.check_call(['touch', '/tmp/district-centroids.geojson'])
      subprocess.check_call(['rm', '/tmp/district-centroids.geojson'])
      # FIXME eventually should be name_en, name_es etc.
      subprocess.check_call(['ogr2ogr', '-lco', 'COORDINATE_PRECISION=4', '-f', 'GeoJSON', '/tmp/district-centroids.geojson', connection_string, '-sql', 'select d.id as district_id, d.country_id as country_id, d.name, d.code, d.is_deprecated, d.is_enclave, c.iso as country_iso, c.iso3 as country_iso3, c.name as country_name, c.name_es as country_name_es, c.name_fr as country_name_fr, c.name_ar as country_name_ar, d.centroid from api_district d join api_country c on d.country_id=c.id where d.centroid is not null'])
    except Exception as e:
      print('Failed to export district centroids', e)
      raise

    try:
      print('Update Mapbox tileset source for districts...')
      subprocess.check_call(['tilesets', 'upload-source', '--replace', 'go-ifrc', 'go-districts-src-1', '/tmp/districts.geojson'])
    except Exception as e:
      print('Failed to update tileset source for districts', e)
      raise

    try:
      print('Update Mapbox tileset for districts... and sleeping a minute')
      subprocess.check_call(['tilesets', 'publish', 'go-ifrc.go-districts-1'])
      time.sleep(60)
    except Exception as e:
      print('Failed to update tileset for districts')
      raise

    try:
      print('Update Mapbox tileset source for district centroids...')
      subprocess.check_call(['tilesets', 'upload-source', '--replace', 'go-ifrc', 'go-district-centroids', '/tmp/district-centroids.geojson'])
    except Exception as e:
      print('Failed to update tileset source for district centroid')
      raise
    try:
      print('Update Mapbox tileset for district centroids... [no sleep]')
      subprocess.check_call(['tilesets', 'publish', 'go-ifrc.go-district-centroids'])
    except Exception as e:
      print('Failed to update tileset for distrct centroids')
      raise
