import csv

from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

from api.models import Admin2, Admin2Geoms, Country, District, DistrictGeoms


class Command(BaseCommand):
    help = "import a shapefile of administrative boundary level 2 data to the GO database. To run, python manage.py import-admin2-data input.shp"  # noqa: E501

    missing_args_message = "Filename is missing. A shapefile with valid admin polygons is required."

    def add_arguments(self, parser):
        parser.add_argument("filename", nargs="+", type=str)
        parser.add_argument("--update-geom", action="store_true", help="Update the geometry of the admin2.")
        parser.add_argument(
            "--update-bbox",
            action="store_true",
            help="Update the bbox of the admin2 geometry. Used if you want to overwrite changes that are made by users via the Django Admin",  # noqa: E501
        )
        parser.add_argument(
            "--update-centroid",
            action="store_true",
            help="Update the centroid of the admin2 geometry. Used if you want to overwrite changes that are made by users via the Django Admin",  # noqa: E501
        )
        parser.add_argument("--import-missing", help="Import missing admin2 boundaries for codes mentioned in this file.")
        parser.add_argument(
            "--import-all", action="store_true", help="Import all  admin2 boundaries in the shapefile, if possible."
        )

    @transaction.atomic
    def handle(self, *args, **options):
        filename = options["filename"][0]
        # a dict to hold all the admin2 that needs to be manually imported
        import_missing = {}
        if options["import_missing"]:
            import_file = csv.DictReader(open(options["import_missing"]), fieldnames=["code", "name"])
            next(import_file)
            for row in import_file:
                code = row["code"]
                name = row["name"]
                import_missing[code] = {"code": code, "name": name}
            print("will import these codes", import_missing.keys())
        else:
            # if no filename is specified, open one to write missing code and names
            missing_filename = "missing-admin2.txt"
            print(f"will write missing admin2 codes to {missing_filename}")
            missing_file = csv.DictWriter(open(missing_filename, "w"), fieldnames=["code", "name"])
            missing_file.writeheader()

        try:
            data = DataSource(filename)
        except Exception:
            raise CommandError("Could not open file")

        # loop through each feature in the shapefile
        for feature in data[0]:
            code = feature.get("code") if "code" in feature.fields else feature.get("pcode")
            name = feature.get("name") if "name" in feature.fields else feature.get("shapeName")
            # admin1_id = feature.get("district_id") if "district_id" in feature.fields else feature.get("admin1_id")
            # local_name = feature.get("local_name") if "local_name" in feature.fields else None
            # local_name_code = feature.get("local_name_code") if "local_name_code" in feature.fields else None
            # alternate_name = feature.get("alternate_name") if "alternate_name" in feature.fields else None
            # alternate_name_code = feature.get("alternate_name_code") if "alternate_name_code" in feature.fields else None

            # FIXME: must make sure code and admin1_id are not null before continuing

            geom_wkt = feature.geom.wkt
            geom = GEOSGeometry(geom_wkt, srid=4326)
            centroid = geom.centroid.wkt
            bbox = geom.envelope.wkt
            # import all shapes for admin2
            if options["import_all"]:
                self.add_admin2(options, "all", feature, geom, centroid, bbox)
            else:
                admin2_objects = Admin2.objects.filter(code=code)
                if len(admin2_objects) == 0:
                    if options["import_missing"]:
                        # if it doesn't exist, add it
                        self.add_admin2(options, import_missing, feature, geom, centroid, bbox)
                    else:
                        missing_file.writerow({"code": code, "name": name})

                # if there are more than one admin2 with the same code, filter also using name
                if len(admin2_objects) > 1:
                    admins2_names = Admin2.objects.filter(code=code, name__icontains=name)
                    # if we get a match, update geometry. otherwise consider this as missing because it's possible the names aren't matching.  # noqa: E501
                    if len(admins2_names):
                        # update geom, centroid and bbox
                        self.update_admin2_columns(options, admins2_names[0], geom, centroid, bbox)
                    else:
                        if options["import_missing"]:
                            # if it doesn't exist, add it
                            self.add_admin2(options, import_missing, feature, geom, centroid, bbox)
                        else:
                            missing_file.writerow({"code": code, "name": name})
                if len(admin2_objects) == 1:
                    self.update_admin2_columns(options, admin2_objects[0], geom, centroid, bbox)
        print("done!")

    @transaction.atomic
    def add_admin2(self, options, import_missing, feature, geom, centroid, bbox):
        code = feature.get("code") if "code" in feature.fields else feature.get("pcode")
        name = feature.get("name") if "name" in feature.fields else feature.get("shapeName")
        admin1_id = feature.get("district_id") if "district_id" in feature.fields else feature.get("admin1_id")
        local_name = feature.get("local_name") if "local_name" in feature.fields else None
        local_name_code = feature.get("local_name_code") if "local_name_code" in feature.fields else None
        alternate_name = feature.get("alternate_name") if "alternate_name" in feature.fields else None
        alternate_name_code = feature.get("alternate_name_code") if "alternate_name_code" in feature.fields else None
        admin2 = Admin2()
        admin2.code = code
        admin2.name = name
        admin2.centroid = centroid
        admin2.bbox = bbox
        admin2.local_name = local_name
        admin2.local_name_code = local_name_code
        admin2.alternate_name = alternate_name
        admin2.alternate_name_code = alternate_name_code

        try:
            admin1 = District.objects.get(id=admin1_id)
            admin2.admin1_id = admin1.id
        except ObjectDoesNotExist:
            print(f"admin1 {admin1_id} not found for - admin2: {name}")
            pass

        # save data
        if admin2.admin1_id is not None and ((import_missing == "all") or (code in import_missing.keys())):
            try:
                print("importing", admin2.name)
                admin2.save()
                if options["update_geom"]:
                    self.update_geom(admin2, geom)
            except IntegrityError:
                print(f"Duplicate object {admin2.name}")
                pass

    def update_geom(self, admin2, geom):
        try:
            Admin2Geom = Admin2Geoms.objects.get(admin2=admin2)
            Admin2Geom.geom = geom
            Admin2Geom.save()
        except ObjectDoesNotExist:
            Admin2Geom = Admin2Geoms()
            Admin2Geom.admin2 = admin2
            Admin2Geom.geom = geom
            Admin2Geom.save()

    def find_district_id(self, centroid, country_iso2):
        """Find district_id for admin2, according to the point with in the district polygon.
        Args:
            centroid (str): Admin2 centroid
            country_iso2 (str): Country iso2
        """
        admin1_id = None
        country_id = Country.objects.get(iso=country_iso2)
        if country_id is not None:
            districts = District.objects.filter(country_id=country_id)
            districts_ids = [d.id for d in districts]
            districts_geoms = DistrictGeoms.objects.filter(district_id__in=districts_ids)
            centroid_geom = GEOSGeometry(centroid, srid=4326)
            for district_geom in districts_geoms:
                if centroid_geom.within(district_geom.geom):
                    admin1_id = district_geom.district_id
                    break
        return admin1_id

    def update_admin2_columns(self, options, admin2, geom, centroid, bbox):
        if options["update_geom"]:
            print(f"Update geom for {admin2.name}")
            self.update_geom(admin2, geom)
        if options["update_centroid"]:
            print(f"Update centroid for {admin2.name}")
            admin2.centroid = centroid
        if options["update_bbox"]:
            print(f"Update bbox for {admin2.name}")
            admin2.bbox = bbox
        admin2.save()
