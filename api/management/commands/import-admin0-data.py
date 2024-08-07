import csv

from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Point
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from api.models import Country, CountryGeoms, Region


class Command(BaseCommand):
    help = "import a shapefile of adminstrative boundary level 0 data to the GO database. To run, python manage.py import-admin0-data input.shp"  # noqa: E501

    missing_args_message = "Filename is missing. A shapefile with valid admin polygons is required."
    region_enum = {"Africa": 0, "Americas": 1, "Asia-Pacific": 2, "Europe": 3, "Middle East and North Africa": 4}

    def add_arguments(self, parser):
        parser.add_argument("filename", nargs="+", type=str)
        parser.add_argument("--update-geom", action="store_true", help="Update the geometry of the country.")
        parser.add_argument(
            "--update-bbox",
            action="store_true",
            help="Update the bbox of the country geometry. Used if you want to overwrite changes that are made by users via the Django Admin",  # noqa: E501
        )
        parser.add_argument(
            "--update-centroid",
            help="Update the centroid of the country using a CSV file provided. If the CSV does not have the country iso, then we use the geometric centroid",  # noqa: E501
        )
        parser.add_argument("--import-missing", help="Import missing countries for iso codes mentioned in this file.")
        parser.add_argument("--update-iso3", help="Import missing iso3 codes from this file.")
        parser.add_argument("--update-independent", action="store_true", help="Update independence status for the country")
        parser.add_argument("--import-all", action="store_true", help="Import all geometries in the given shapefile.")

    @transaction.atomic
    def handle(self, *args, **options):
        filename = options["filename"][0]

        import_missing = []

        if options["import_missing"]:
            import_file = open(options["import_missing"], "r")
            import_missing = import_file.read().splitlines()
            print("will import these isos if found", import_missing)
        else:
            print("will write missing country iso to missing-countries.txt")
            missing_file = open("missing-countries.txt", "w")
            duplicate_file = open("duplicate-countries.txt", "w")

        country_centroids = {}
        if options["update_centroid"]:
            centroid_file = csv.DictReader(
                open(options["update_centroid"], "r"), fieldnames=["country", "latitude", "longitude", "name"]
            )
            next(centroid_file)
            for row in centroid_file:
                code = row["country"]
                lat = row["latitude"]
                lon = row["longitude"]
                if lat != "" and lon != "":
                    country_centroids[code] = Point(float(lon), float(lat))

        iso3_codes = {}
        if options["update_iso3"]:
            iso3_file = csv.DictReader(open(options["update_iso3"], "r"), fieldnames=["iso2", "iso3"])
            next(iso3_file)
            for row in iso3_file:
                iso3_codes[row["iso2"]] = row["iso3"]

        try:
            data = DataSource(filename)
        except Exception:
            raise CommandError("Could not open file")

        fields = data[0].fields
        # first, let's import all the geometries for countries with iso code
        for feature in data[0]:
            feature_iso2 = feature.get("ISO2")
            geom_wkt = feature.geom.wkt
            geom = GEOSGeometry(geom_wkt, srid=4326)
            if geom.geom_type == "Polygon":
                geom = MultiPolygon(geom)

            centroid = geom.centroid.wkt
            bbox = geom.envelope.geojson

            if feature_iso2:
                # find this country in the database
                try:
                    # if the country exist
                    country = Country.objects.get(iso=feature_iso2, record_type=1)

                    if options["update_geom"]:
                        # check if this geom exists
                        try:
                            CountryGeom = CountryGeoms.objects.get(country=country)
                            CountryGeom.geom = geom.wkt
                            CountryGeom.save()
                        except ObjectDoesNotExist:
                            # add geom
                            CountryGeom = CountryGeoms()
                            CountryGeom.country = country
                            CountryGeom.geom = geom.wkt
                            CountryGeom.save()

                    if options["update_bbox"]:
                        # add bbox
                        country.bbox = bbox

                    if options["update_centroid"]:
                        # add centroid
                        if feature_iso2 in country_centroids.keys():
                            country.centroid = country_centroids[feature_iso2]
                        else:
                            country.centroid = centroid

                    if options["update_iso3"]:
                        if feature_iso2 in iso3_codes.keys():
                            print("updating iso3", iso3_codes[feature_iso2])
                            country.iso3 = iso3_codes[feature_iso2]

                    if options["update_independent"]:
                        if "INDEPENDEN" in fields:
                            independent = feature.get("INDEPENDEN")
                            if independent == "TRUE":
                                country.independent = True
                            elif independent == "FALSE":
                                country.independent = False
                            else:
                                country.independent = None

                    # save
                    if (
                        options["update_geom"]
                        or options["update_bbox"]
                        or options["update_centroid"]
                        or options["update_iso3"]
                        or options["update_independent"]
                    ):
                        print("updating %s" % feature_iso2)
                        country.save()

                except MultipleObjectsReturned:
                    if not options["import_missing"]:
                        name = feature.get("NAME_ICRC")
                        duplicate_file.write(feature_iso2 + "\n")
                        print("duplicate country", feature_iso2, name)

                except ObjectDoesNotExist:
                    if not options["import_missing"]:
                        name = feature.get("NAME_ICRC")
                        missing_file.write(feature_iso2 + "\n")
                        print("missing country", feature_iso2, name)
                    else:
                        # check if this iso exists in the import list
                        if feature_iso2 in import_missing:
                            print("importing", feature_iso2)
                            self.add_country(feature, geom, centroid, bbox, feature_iso2, fields)
                        else:
                            print("skipping", feature_iso2)
            else:
                if options["import_all"]:
                    print("Geometry with no iso code found, but will still import.")
                    self.add_country(feature, geom, centroid, bbox, None, fields)
        print("done!")

    def add_country(self, feature, geom, centroid, bbox, iso, fields):
        # new country object
        country = Country()

        name = feature.get("NAME_ICRC")
        iso3 = feature.get("ISO3")

        region = feature.get("REGION_IFR")
        # get region from db
        region_id = Region.objects.get(name=self.region_enum[region])

        if "INDEPENDEN" in fields:
            independent = feature.get("INDEPENDEN")
            if independent == "TRUE":
                country.independent = True
            elif independent == "FALSE":
                country.independent = False
            else:
                country.independent = None

        if "NATIONAL_S" in fields:
            country.society_name = feature.get("NATIONAL_S")

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
