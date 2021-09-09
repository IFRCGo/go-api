import subprocess
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

class Command(BaseCommand):
  help = "This command produces a countries.geojson and districts.geojson, and uploads them to Mapbox. It is the source for all GO Maps."

  def handle(self, *args, **options):
    try:
      db = settings.DATABASES['default']
      DB_HOST = db['HOST']
      DB_NAME = db['NAME']
      DB_USER = db['USER']
      DB_PASSWORD = db['PASSWORD']
      DB_PORT = 5432
      connection_string = 'PG:host={} dbname={} user={} password={} port={}'.format(DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT)

      print('Exporting countries...')
      subprocess.check_call(['touch', '/tmp/countries.geojson'])
      subprocess.check_call(['rm', '/tmp/countries.geojson'])
      subprocess.check_call(['ogr2ogr', '-f', 'GeoJSON', '/tmp/countries.geojson', connection_string, '-sql', 'select cd.country_id, cd.geom, c.name, c.name_es, c.name_fr, c.name_ar, c.iso, c.region_id, c.iso3, c.independent, c.is_deprecated, c.disputed, c.fdrs, c.record_type from api_countrygeoms cd, api_country c where cd.country_id = c.id and c.record_type=1' ])
      print('Countries written to /tmp/countries.geojson')

      print('Exporting districts...')
      subprocess.check_call(['touch', '/tmp/districts.geojson'])
      subprocess.check_call(['rm', '/tmp/districts.geojson'])
      # FIXME eventually should be name_en, name_es etc.
      subprocess.check_call(['ogr2ogr', '-lco', 'COORDINATE_PRECISION=5', '-f', 'GeoJSON', '/tmp/districts.geojson', connection_string, '-sql', 'select cd.district_id, cd.geom, c.name, c.code, c.country_id, c.is_enclave, c.is_deprecated, country.iso as country_iso, country.iso3 as country_iso3, country.name as country_name, country.name_es as country_name_es, country.name_fr as country_name_fr, country.name_ar as country_name_ar from api_districtgeoms cd, api_district c, api_country country where cd.district_id = c.id and cd.geom is not null and country.id=c.country_id' ])
      print('Districts written to /tmp/districts.geojson')

      print('Exporting country centroids...')
      subprocess.check_call(['touch', '/tmp/country-centroids.geojson'])
      subprocess.check_call(['rm', '/tmp/country-centroids.geojson'])
      subprocess.check_call(['ogr2ogr', '-lco', 'COORDINATE_PRECISION=4', '-f', 'GeoJSON', '/tmp/country-centroids.geojson', connection_string, '-sql', 'select id as country_id, name_en, name_ar, name_es, name_fr, independent, disputed, is_deprecated, iso, iso3, record_type, centroid from api_country where centroid is not null'])

      print('Exporting district centroids...')
      subprocess.check_call(['touch', '/tmp/district-centroids.geojson'])
      subprocess.check_call(['rm', '/tmp/district-centroids.geojson'])
      # FIXME eventually should be name_en, name_es etc.
      subprocess.check_call(['ogr2ogr', '-lco', 'COORDINATE_PRECISION=4', '-f', 'GeoJSON', '/tmp/district-centroids.geojson', connection_string, '-sql', 'select d.id as district_id, d.name, d.code, d.is_deprecated, d.is_enclave, c.iso as country_iso, c.iso3 as country_iso3, c.name as country_name, c.name_es as country_name_es, c.name_fr as country_name_fr, c.name_ar as country_name_ar, d.centroid from api_district d join api_country c on d.country_id=c.id where d.centroid is not null'])

      print('Update Mapbox tileset source for countries...')
      subprocess.check_call(['tilesets', 'upload-source', '--replace', 'go-ifrc', 'go-countries-src', '/tmp/countries.geojson'])

      print('Update Mapbox tileset for countries...')
      subprocess.check_call(['tilesets', 'publish', 'go-ifrc.go-countries'])


      print('Update Mapbox tileset source for districts...')
      subprocess.check_call(['tilesets', 'upload-source', '--replace', 'go-ifrc', 'go-districts-src-1', '/tmp/districts.geojson'])

      print('Update Mapbox tileset for districts...')
      subprocess.check_call(['tilesets', 'publish', 'go-ifrc.go-districts-1'])

      print('Update Mapbox tileset source for country centroids...')
      subprocess.check_call(['tilesets', 'upload-source', '--replace', 'go-ifrc', 'go-country-centroids', '/tmp/country-centroids.geojson'])

      print('Update Mapbox tileset for country centroids...')
      subprocess.check_call(['tilesets', 'publish', 'go-ifrc.go-country-centroids'])

      print('Update Mapbox tileset source for district centroids...')
      subprocess.check_call(['tilesets', 'upload-source', '--replace', 'go-ifrc', 'go-district-centroids', '/tmp/district-centroids.geojson'])

      print('Update Mapbox tileset for district centroids...')
      subprocess.check_call(['tilesets', 'publish', 'go-ifrc.go-district-centroids'])
    except BaseException as e:
      raise CommandError('Could not update tilesets: ' + str(e))