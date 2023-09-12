from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos import MultiPolygon
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import transaction
from api.models import Country
from api.models import CountryGeoms


class Command(BaseCommand):
    help = "update admin0 geometries from a shapefile that has ICRC column headers along with ids from Go database. To run, python manage.py update-admin0-with-id input.shp"

    missing_args_message = "Filename is missing."

    def add_arguments(self, parser):
        parser.add_argument("filename", nargs="+", type=str)

    @transaction.atomic
    def handle(self, *args, **options):
        filename = options["filename"][0]

        try:
            data = DataSource(filename)
        except:
            raise CommandError("Could not open file")

        for feature in data[0]:
            feature_id = feature.get("id")
            geom_wkt = feature.geom.wkt
            geom = GEOSGeometry(geom_wkt, srid=4326)
            if geom.geom_type == "Polygon":
                geom = MultiPolygon(geom)

            if feature_id:
                # find this country
                try:
                    country = Country.objects.get(id=feature_id)
                    try:
                        # update if geometry exists
                        CountryGeom = CountryGeoms.objects.get(country=country)
                        CountryGeom.geom = geom.wkt
                        print("Updating geometry for %s" % feature_id)
                        CountryGeom.save()
                    except ObjectDoesNotExist:
                        # add geom
                        CountryGeom = CountryGeoms()
                        CountryGeom.country = country
                        CountryGeom.geom = geom.wkt
                        print("Creating geometry for %s" % feature_id)
                        CountryGeom.save()
                except ObjectDoesNotExist:
                    print("%s does not exist" % feature_id)
                except MultipleObjectsReturned:
                    print("%s has more than one geometry, will delete and create a new one")
                    CountryGeom.objects.filter(country=country).delete()
                    CountryGeom = CountryGeoms()
                    CountryGeom.country = country
                    CountryGeom.geom = geom.wkt
                    print("Creating geometry for %s" % feature_id)
                    CountryGeom.save()

        print("Done!")
