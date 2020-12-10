import sys
import os
import csv
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos import MultiPolygon
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from api.models import Country
from api.models import District
from api.models import DistrictGeoms

class Command(BaseCommand):
  help = "import a shapefile of administrative boundary level 1 data to the GO database. To run, python manage.py import-admin1-data input.shp"

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
      help='Update the bbox of the district geometry. Used if you want to overwrite changes that are made by users via the Django Admin'
      )
    parser.add_argument(
      '--update-centroid',
      action='store_true',
      help='Update the centroid of the district geometry. Used if you want to overwrite changes that are made by users via the Django Admin'
      )
    parser.add_argument(
      '--import-missing',
      help='Import missing districts for codes mentioned in this file.'
      )
    parser.add_argument(
      '--import-all',
      action='store_true',
      help='Import all districts in the shapefile, if possible.'
    )

  @transaction.atomic
  def handle(self, *args, **options):
    filename = options['filename'][0]

    # a dict to hold all the districts that needs to be manually imported
    import_missing = {}
    if options['import_missing']:
      import_file = csv.DictReader(open(options['import_missing']), fieldnames=['code', 'name'])
      next(import_file)
      for row in import_file:
        code = row['code']
        name = row['name']
        import_missing[code] = {
          'code': code,
          'name': name
        }
      print('will import these codes', import_missing.keys())
    else:
      # if no filename is specified, open one to write missing code and names
      print('will write missing district codes to missing-districts.txt')
      missing_file = csv.DictWriter(open('missing-districts.txt', 'w'), fieldnames=['code', 'name'])
      missing_file.writeheader()

    try:
      data = DataSource(filename)
    except:
      raise CommandError('Could not open file')

    # loop through each feature in the shapefile
    for feature in data[0]:
      code = feature.get('ADMIN01COD')
      name = feature.get('ADMIN01NAM')
      country_iso2 = feature.get('ISO2')
      country_name = feature.get('COUNTRY')

      geom_wkt = feature.geom.wkt
      geom = GEOSGeometry(geom_wkt, srid=4326)
      if (geom.geom_type == 'Polygon'):
          geom = MultiPolygon(geom)

      centroid = geom.centroid.wkt
      bbox = geom.envelope.wkt

      # if there is no code, but import all is flagged then import this district
      if code is None or code == '':
        if options['import_all']:
          self.add_district(options, 'all', feature, geom, centroid, bbox)

      # for features that has a code and not NA
      if code and code != 'N.A':
        districts = District.objects.filter(code=code)
        if len(districts) == 0:
          if options['import_missing']:
            # if it doesn't exist, add it
            self.add_district(options, import_missing, feature, geom, centroid, bbox)
          else:
            missing_file.writerow({'code': code, 'name': name})

        # if there are more than one district with the same code, filter also using name
        if len(districts) > 1:
          district = District.objects.filter(code=code, name__icontains=name)
          # if we get a match, update geometry. otherwise consider this as missing because it's possible the names aren't matching.
          if len(district):
            # update geom, centroid and bbox
            d = district[0]
            if options['update_geom']:
              self.update_geom(d, geom)
            if options['update_centroid']:
              d.centroid = centroid
            if options['update_bbox']:
              d.bbox = bbox
            d.save()
          else:
            if options['import_missing']:
              # if it doesn't exist, add it
              self.add_district(options, import_missing, feature, geom, centroid, bbox)
            else:
              missing_file.writerow({'code': code, 'name': name})

          
        if len(districts) == 1:
          d = districts[0]
          if options['update_geom']:
            self.update_geom(d, geom)
          if options['update_centroid']:
            d.centroid = centroid
          if options['update_bbox']:
            d.bbox = bbox
          d.save()

      if code == 'N.A':
        district = District.objects.filter(name__icontains=name)
        if len(district):
          d = district[0]
          if options['update_geom']:
            self.update_geom(d, geom)
          if options['update_centroid']:
            d.centroid = centroid
          if options['update_bbox']:
            d.bbox = bbox
          d.save()
        else:
          if options['import_missing']:
            self.add_district(options, import_missing, feature, geom, centroid, bbox)
          else:
            missing_file.writerow({'code': code, 'name': name})



      if code == 'f':
        district = District.objects.filter(name__icontains=name)
        if not len(district):
          if options['import_missing']:
            self.add_district(options, import_missing, feature, geom, centroid, bbox)
          else:
            missing_file.writerow({'code': code, 'name': name})

    print('done!')


  def add_district(self, options, import_missing, feature, geom, centroid, bbox):
    code = feature.get('ADMIN01COD') or 'N.A'
    name = feature.get('ADMIN01NAM')
    district = District()
    district.code = code
    district.name = name
    district.country_iso = feature.get('ISO2')
    district.country_name = feature.get('COUNTRY')
    district.centroid = centroid
    district.bbox = bbox
    try:
      # find the country based on country iso
      country_id = Country.objects.get(iso=feature.get('ISO2').lower())
      district.country = country_id
    except ObjectDoesNotExist:
      print('country does not exist', feature.get('ISO2').lower())
      pass

    if (import_missing == 'all'):
      print('importing', district.name)
      district.save()
      if (options['update_geom']):
        self.update_geom(district, geom)
    elif (code in import_missing.keys()):
      district.save()
      if (options['update_geom']):
        self.update_geom(district, geom)
    else:
      print('skipping', code)

  def update_geom(self, district, geom):
      DistrictGeom = DistrictGeoms()
      DistrictGeom.district = district
      DistrictGeom.geom = geom
      DistrictGeom.save()