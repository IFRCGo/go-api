import sys
import os
import csv
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos import MultiPolygon
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from api.models import Country
from api.models import District
from api.models import DistrictGeoms
from api.models import Admin2
from api.models import Admin2Geoms

class Command(BaseCommand):
  help = "import a shapefile of administrative boundary level 2 data to the GO database. To run, python manage.py import-admin2-data input.shp"

  missing_args_message = "Filename is missing. A shapefile with valid admin polygons is required."

  def add_arguments(self, parser):
    parser.add_argument('filename', nargs='+', type=str)
    parser.add_argument(
      '--update-geom',
      action='store_true',
      help='Update the geometry of the admin2.'
      )
    parser.add_argument(
      '--update-bbox',
      action='store_true',
      help='Update the bbox of the admin2 geometry. Used if you want to overwrite changes that are made by users via the Django Admin'
      )
    parser.add_argument(
      '--update-centroid',
      action='store_true',
      help='Update the centroid of the admin2 geometry. Used if you want to overwrite changes that are made by users via the Django Admin'
      )
    parser.add_argument(
      '--import-missing',
      help='Import missing admin2 boundaries for codes mentioned in this file.'
      )
    parser.add_argument(
      '--import-all',
      action='store_true',
      help='Import all  admin2 boundaries in the shapefile, if possible.'
    )

  @transaction.atomic
  def handle(self, *args, **options):
    filename = options['filename'][0]
  
    # a dict to hold all the admin2 that needs to be manually imported
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
      missing_filename="missing-admin2.txt"
      print(f'will write missing admin2 codes to {missing_filename}')
      missing_file = csv.DictWriter(open(missing_filename, 'w'), fieldnames=['code', 'name'])
      missing_file.writeheader()

    try:
      data = DataSource(filename)
    except:
      raise CommandError('Could not open file')

    # loop through each feature in the shapefile
    for feature in data[0]:
      code = feature.get('code')
      name = feature.get('name')
      geom_wkt = feature.geom.wkt
      geom = GEOSGeometry(geom_wkt, srid=4326)
      if (geom.geom_type == 'Polygon'):
          geom = MultiPolygon(geom)

      centroid = geom.centroid.wkt
      bbox = geom.envelope.wkt
      # if there is no code, but import all is flagged then import this admin2
      if code is None or code == '':
        if options['import_all']:
          self.add_admin2(options, 'all', feature, geom, centroid, bbox)

      # for features that has a code and not NA
      if code and code != 'N.A':
        admin2_objects = Admin2.objects.filter(code=code)
        if len(admin2_objects) == 0:
          if options['import_missing']:
            # if it doesn't exist, add it
            self.add_admin2(options, import_missing, feature, geom, centroid, bbox)
          else:
            missing_file.writerow({'code': code, 'name': name})

        # if there are more than one admin2 with the same code, filter also using name
        if len(admin2_objects) > 1:
          admins2_names = Admin2.objects.filter(code=code, name__icontains=name)
          # if we get a match, update geometry. otherwise consider this as missing because it's possible the names aren't matching.
          if len(admins2_names):
            # update geom, centroid and bbox
            d = admins2_names[0]
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
              self.add_admin2(options, import_missing, feature, geom, centroid, bbox)
            else:
              missing_file.writerow({'code': code, 'name': name})


        if len(admin2_objects) == 1:
          d = admin2_objects[0]
          if options['update_geom']:
            self.update_geom(d, geom)
          if options['update_centroid']:
            d.centroid = centroid
          if options['update_bbox']:
            d.bbox = bbox
          d.save()

      if code == 'N.A':
        admin2 = Admin2.objects.filter(name__icontains=name)
        if len(admin2):
          d = admin2[0]
          if options['update_geom']:
            self.update_geom(d, geom)
          if options['update_centroid']:
            d.centroid = centroid
          if options['update_bbox']:
            d.bbox = bbox
          d.save()
        else:
          if options['import_missing']:
            self.add_admin2(options, import_missing, feature, geom, centroid, bbox)
          else:
            missing_file.writerow({'code': code, 'name': name})

      if code == 'f':
        admin2 = Admin2.objects.filter(name__icontains=name)
        if not len(admin2):
          if options['import_missing']:
            self.add_admin2(options, import_missing, feature, geom, centroid, bbox)
          else:
            missing_file.writerow({'code': code, 'name': name})

    print('done!')


  def add_admin2(self, options, import_missing, feature, geom, centroid, bbox):
    code = feature.get('code') or 'N.A'
    name = feature.get('name')
    admin2 =Admin2()
    admin2.code = code
    admin2.name = name
    admin2.centroid = centroid
    admin2.bbox = bbox
    try:
      # find district_id based on centroid of admin2 and country.
      admin1_id = self.find_district_id(centroid)
      if admin1_id is None:
        pass
      admin2.admin1_id = admin1_id
    except ObjectDoesNotExist:
      print('country does not exist', "af")
      pass

    if (import_missing == 'all') or (code in import_missing.keys()):
      print('importing', admin2.name)
      admin2.save()
      if (options['update_geom']):
        self.update_geom(admin2, geom)

  def update_geom(self, admin2, geom):
      try:
        Admin2Geom = Admin2Geoms.objects.get(admin2=admin2)
        Admin2Geom.geom = geom
        Admin2Geom.save()
      except ObjectDoesNotExist:
        Admin2Geom = DistrictGeoms()
        Admin2Geom.admin2 = admin2
        Admin2Geom.geom = geom
        Admin2Geom.save()

  def find_district_id(self, centroid):
      """Find district_id for admin2, according to the point with in the district polygon.
      Args:
          centroid (str): Admin2 centroid
      """
      admin1_id = None
      country_id = Country.objects.get(iso="af")
      districts = District.objects.filter(country_id=country_id)
      districts_ids = [d.id for d in districts]
      districts_geoms = DistrictGeoms.objects.filter(district_id__in=districts_ids)
      centroid_geom = GEOSGeometry(centroid, srid=4326)
      for district_geom in districts_geoms:
          if centroid_geom.within(district_geom.geom):
              admin1_id = district_geom.district_id
              break
      return admin1_id