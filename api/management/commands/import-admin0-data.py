import sys
import os
import json
import csv
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos import MultiPolygon, Point
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import transaction
from api.models import Country
from api.models import Region

class Command(BaseCommand):
  help = "import a shapefile of adminstrative boundary level 0 data to the GO database. To run, python manage.py import-admin0-data input.shp"

  missing_args_message = "Filename is missing. A shapefile with valid admin polygons is required."

  def add_arguments(self, parser):
    parser.add_argument('filename', nargs='+', type=str)
    parser.add_argument(
    '--update-geom',
    action='store_true',
    help='Update the geometry of the district.'
    )
    parser.add_argument(
      '--update-bbox',
      action='store_true',
      help='Update the bbox of the country geometry. Used if you want to overwrite changes that are made by users via the Django Admin'
      )
    parser.add_argument(
      '--update-centroid',
      help='Update the centroid of the country using a CSV file provided. If the CSV does not have the country iso, then we use the geometric centroid'
      )
    parser.add_argument(
      '--import-missing',
      help='Import missing countries for iso codes mentioned in this file.'
      )

  @transaction.atomic
  def handle(self, *args, **options):
    filename = options['filename'][0]

    region_enum = {
      'Africa': 0,
      'Americas': 1,
      'Asia-Pacific': 2,
      'Europe': 3,
      'Middle East and North Africa': 4
    }

    import_missing = []

    if options['import_missing']:
      import_file = open(options['import_missing'], 'r')
      import_missing = import_file.read().splitlines()
      print('will import these isos if found', import_missing)
    else:
      print('will write missing country iso to missing-countries.txt')
      missing_file = open('missing-countries.txt', 'w')
      duplicate_file = open('duplicate-countries.txt', 'w')

    country_centroids = {}
    if options['update_centroid']:
      centroid_file = csv.DictReader(open(options['update_centroid'], 'r'), fieldnames=['country', 'latitude', 'longitude', 'name'])
      next(centroid_file)
      for row in centroid_file:
        code = row['country'].lower()
        lat = row['latitude']
        lon = row['longitude']
        if (lat != '' and lon != ''):
          country_centroids[code] = Point(float(lon), float(lat))

    try:
      data = DataSource(filename)
    except:
      raise CommandError('Could not open file')

    fields = data[0].fields
    # first, let's import all the geometries for countries with iso code
    for feature in data[0]:
      feature_iso2 = feature.get('ISO2').lower()

      if feature_iso2:
        geom_wkt = feature.geom.wkt
        geom = GEOSGeometry(geom_wkt, srid=4326)
        if (geom.geom_type == 'Polygon'):
          geom = MultiPolygon(geom)

        centroid = geom.centroid.wkt
        bbox = geom.envelope.geojson

        # find this country in the database
        try:
          # if the country exist
          country = Country.objects.get(iso=feature_iso2, record_type=1)

          if options['update_geom']:
            # add geom
            country.geom = geom.wkt

          if options['update_bbox']:
            # add bbox
            country.bbox = bbox

          if options['update_centroid']:
            # add centroid
            if (feature_iso2 in country_centroids.keys()):
              country.centroid = country_centroids[feature_iso2]
            else:
              country.centroid = centroid

          # save
          if options['update_geom'] or options['update_bbox'] or options['update_centroid']:
            print('updating %s with geometries' %feature_iso2)
            country.save()

        except MultipleObjectsReturned:
          if not options['import_missing']:
            name = feature.get('NAME_ICRC')
            duplicate_file.write(feature_iso2 + '\n')
            print('duplicate country', feature_iso2, name)

        except ObjectDoesNotExist:
          if not options['import_missing']:
            name = feature.get('NAME_ICRC')
            missing_file.write(feature_iso2 + '\n')
            print('missing country', feature_iso2, name)
          else:
            # check if this iso exists in the import list
            if feature_iso2 in import_missing:
              print('importing', feature_iso2)
              # new country object
              country = Country()

              record_type = 1 # country
              name = feature.get('NAME_ICRC')
              iso = feature_iso2
              iso3 = feature.get('ISO3').lower()

              region = feature.get('REGION_IFR')
              # get region from db
              region_id = Region.objects.get(name=region_enum[region])

              if ('INDEPENDEN' in fields):
                independent = feature.get('INDEPENDEN')
                if independent == 'TRUE':
                    country.independent = True
                elif independent == 'FALSE':
                    country.independent = False
                else:
                  country.independent = None

              if ('NATIONAL_S' in fields):
                country.society_name = feature.get('NATIONAL_S')

              country.name = name
              country.record_type = 1
              country.iso = iso
              country.iso3 = iso3
              country.region = region_id
              country.geom = geom.wkt
              country.centroid = centroid
              country.bbox = bbox

              # save
              country.save()
            else:
              print('skipping', feature_iso2)
    
    print('done!')



