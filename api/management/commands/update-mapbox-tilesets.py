import os
import subprocess
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "This command produces a countries.geojson and districts.geojson, and uploads them to Mapbox. It is the source for all GO Maps."  # noqa: E501

    missing_args_message = "Argument missing. Specify --update-countries, --update-districts or --update-all."

    def add_arguments(self, parser):
        parser.add_argument("--update-countries", action="store_true", help="Update tileset for countries")
        parser.add_argument("--update-districts", action="store_true", help="Update tileset for districts")
        parser.add_argument("--create-and-update-admin2", help="Create and update admin2 tileset for this country ISO")
        parser.add_argument("--update-admin2", help="Update admin2 tileset for this country ISO")
        parser.add_argument("--update-all", action="store_true", help="Update tileset for countries and districts")
        parser.add_argument("--production", action="store_true", help="Update production tilesets. Default is staging")

    db = settings.DATABASES["default"]
    DB_HOST = db["HOST"]
    DB_NAME = db["NAME"]
    DB_USER = db["USER"]
    DB_PASSWORD = db["PASSWORD"]
    DB_PORT = 5432
    connection_string = "PG:host={} dbname={} user={} password={} port={}".format(DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT)

    def handle(self, *args, **options):
        try:
            if os.getenv("MAPBOX_ACCESS_TOKEN") is None:
                raise Exception("MAPBOX_ACCESS_TOKEN must be set")

            staging = True
            if options["production"]:
                staging = False

            if options["update_countries"] or options["update_all"]:
                self.update_countries(staging)

            if options["update_districts"] or options["update_all"]:
                self.update_districts(staging)

            if options["create_and_update_admin2"]:
                print(f'Creating source for {options["create_and_update_admin2"]}')
                self.create_and_update_admin2(options["create_and_update_admin2"], staging)

            if options["update_admin2"]:
                print(f'Updating tileset for {options["update_admin2"]}')
                self.publish_admin2(options["update_admin2"], staging, False)

        except BaseException as e:
            raise CommandError("Could not update tilesets: " + str(e))

    def update_countries(self, staging):
        try:
            print("Exporting countries...")

            try:
                os.remove("/tmp/countries.geojson")
            except FileNotFoundError:
                pass

            subprocess.check_call(
                [
                    "ogr2ogr",
                    "-f",
                    "GeoJSON",
                    "/tmp/countries.geojson",
                    self.connection_string,
                    "-sql",
                    "select cd.country_id, cd.geom, c.name, c.name_es, c.name_fr, c.name_ar, c.iso, c.region_id, c.iso3, c.independent, c.is_deprecated, c.disputed, c.fdrs, c.record_type from api_countrygeoms cd, api_country c where cd.country_id = c.id and c.record_type=1",  # noqa: E501
                ]
            )
            print("Countries written to /tmp/countries.geojson")
        except Exception as e:
            print("Failed to export countries", e)
            raise

        try:
            print("Exporting country centroids...")

            try:
                os.remove("/tmp/country-centroids.geojson")
            except FileNotFoundError:
                pass

            subprocess.check_call(
                [
                    "ogr2ogr",
                    "-lco",
                    "COORDINATE_PRECISION=4",
                    "-f",
                    "GeoJSON",
                    "/tmp/country-centroids.geojson",
                    self.connection_string,
                    "-sql",
                    "select id as country_id, name_en as name, name_ar, name_es, name_fr, independent, disputed, is_deprecated, iso, iso3, record_type, fdrs, region_id, centroid from api_country where centroid is not null",  # noqa: E501
                ]
            )
        except Exception as e:
            print("Failed to export country centroids", e)
            raise

        try:
            print("Update Mapbox tileset source for countries...")
            tileset_source_name = "go-countries-src-staging" if staging else "go-countries-src"
            subprocess.check_call(
                ["tilesets", "upload-source", "--replace", "go-ifrc", tileset_source_name, "/tmp/countries.geojson"]
            )
        except Exception as e:
            print("Failed to update tileset source for countries", e)
            raise

        try:
            print("Update Mapbox tileset for countries... and sleeping a minute")
            tileset_name = "go-ifrc.go-countries-staging" if staging else "go-ifrc.go-countries"
            subprocess.check_call(["tilesets", "publish", tileset_name])
            time.sleep(60)
        except Exception as e:
            print("Failed to update tileset for countries", e)
            raise

        try:
            print("Update Mapbox tileset source for country centroids...")
            tileset_source_name = "go-country-centroids-staging" if staging else "go-country-centroids"
            subprocess.check_call(
                [
                    "tilesets",
                    "upload-source",
                    "--replace",
                    "go-ifrc",
                    "go-country-centroids",
                    "/tmp/country-centroids.geojson",
                ]
            )
        except Exception:
            print("Failed to update tileset source for country centroids")
            raise

        try:
            print("Update Mapbox tileset for country centroids... and sleeping a minute")
            tileset_name = "go-ifrc.go-country-centroids-staging" if staging else "go-ifrc.go-country-centroids"
            subprocess.check_call(["tilesets", "publish", tileset_name])
            time.sleep(60)
        except Exception:
            print("Failed to update tileset for country centroids")
            raise

    def update_districts(self, staging):
        try:
            print("Exporting districts...")

            try:
                os.remove("/tmp/distrcits.geojson")
            except FileNotFoundError:
                pass

            # FIXME eventually should be name_en, name_es etc.
            subprocess.check_call(
                [
                    "ogr2ogr",
                    "-lco",
                    "COORDINATE_PRECISION=5",
                    "-f",
                    "GeoJSON",
                    "/tmp/districts.geojson",
                    self.connection_string,
                    "-sql",
                    "select cd.district_id, cd.geom, c.name, c.code, c.country_id, c.is_enclave, c.is_deprecated, country.iso as country_iso, country.iso3 as country_iso3, country.name as country_name, country.name_es as country_name_es, country.name_fr as country_name_fr, country.name_ar as country_name_ar from api_districtgeoms cd, api_district c, api_country country where cd.district_id = c.id and cd.geom is not null and country.id=c.country_id",  # noqa: E501
                ]
            )
            print("Districts written to /tmp/districts.geojson")
        except Exception as e:
            print("Failed to export districts", e)
            raise

        try:
            print("Exporting district centroids...")

            try:
                os.remove("/tmp/district-centroids.geojson")
            except FileNotFoundError:
                pass

            # FIXME eventually should be name_en, name_es etc.
            subprocess.check_call(
                [
                    "ogr2ogr",
                    "-lco",
                    "COORDINATE_PRECISION=4",
                    "-f",
                    "GeoJSON",
                    "/tmp/district-centroids.geojson",
                    self.connection_string,
                    "-sql",
                    "select d.id as district_id, d.country_id as country_id, d.name, d.code, d.is_deprecated, d.is_enclave, c.iso as country_iso, c.iso3 as country_iso3, c.name as country_name, c.name_es as country_name_es, c.name_fr as country_name_fr, c.name_ar as country_name_ar, d.centroid from api_district d join api_country c on d.country_id=c.id where d.centroid is not null",  # noqa: E501
                ]
            )
        except Exception as e:
            print("Failed to export district centroids", e)
            raise

        try:
            print("Update Mapbox tileset source for districts...")
            tileset_source_name = "go-districts-src-staging" if staging else "go-districts-src-1"
            subprocess.check_call(
                ["tilesets", "upload-source", "--replace", "go-ifrc", tileset_source_name, "/tmp/districts.geojson"]
            )
        except Exception as e:
            print("Failed to update tileset source for districts", e)
            raise

        try:
            print("Update Mapbox tileset for districts... and sleeping a minute")
            tileset_name = "go-ifrc.go-districts-staging" if staging else "go-ifrc.go-districts-1"
            subprocess.check_call(["tilesets", "publish", tileset_name])
            time.sleep(60)
        except Exception:
            print("Failed to update tileset for districts")
            raise

        try:
            print("Update Mapbox tileset source for district centroids...")
            tileset_source_name = "go-district-centroids-staging" if staging else "go-district-centroids"
            subprocess.check_call(
                ["tilesets", "upload-source", "--replace", "go-ifrc", tileset_source_name, "/tmp/district-centroids.geojson"]
            )
        except Exception:
            print("Failed to update tileset source for district centroid")
            raise
        try:
            print("Update Mapbox tileset for district centroids... [no sleep]")
            tileset_name = "go-ifrc.go-district-centroids-staging" if staging else "go-ifrc.go-district-centroids"
            subprocess.check_call(["tilesets", "publish", tileset_name])
        except Exception:
            print("Failed to update tileset for distrct centroids")
            raise

    def create_and_update_admin2(self, iso, staging=True):
        # create a new tileset source

        status = self.prepare_admin2_geojson(iso)
        if status:
            update_status = self.update_admin2(iso, staging)
            if update_status:
                polygon_tileset_name = f"go-ifrc.go-admin2-{iso}-staging"
                polygon_recipe_name = f"mapbox/admin2/{iso}-staging.json"
                centroids_tileset_name = f"go-ifrc.go-admin2-{iso}-centroids"
                centroids_recipe_name = f"mapbox/admin2/{iso}-centroids.json"
                if not staging:
                    polygon_tileset_name = f"go-ifrc.go-admin2-{iso}"
                    polygon_recipe_name = f"mapbox/admin2/{iso}.json"

                create_status = subprocess.run(
                    [
                        "tilesets",
                        "create",
                        polygon_tileset_name,
                        "--recipe",
                        polygon_recipe_name,
                        "--name",
                        f"GO Admin2 {iso}",
                    ]
                )

                if create_status:
                    create_status = subprocess.run(
                        [
                            "tilesets",
                            "create",
                            centroids_tileset_name,
                            "--recipe",
                            centroids_recipe_name,
                            "--name",
                            f"GO Admin2 {iso} Centroids",
                        ]
                    )

                if create_status:
                    publish_status = self.publish_admin2(iso, staging, create=True)
                return publish_status

    def update_admin2(self, iso, staging=True):
        # update tileset source
        # update tileset and publish
        polygon_tileset_source__name = f"go-admin2-{iso}-src-staging"
        centroids_tileset_source_name = f"go-admin2-{iso}-centroids-src"
        if not staging:
            polygon_tileset_source__name = f"go-admin2-{iso}-src"

        print("Tileset source", polygon_tileset_source__name)
        print("Tileset source centroids", centroids_tileset_source_name)
        status = self.prepare_admin2_geojson(iso)
        if status:
            status = subprocess.run(
                ["tilesets", "upload-source", "--replace", "go-ifrc", polygon_tileset_source__name, f"/tmp/{iso}.geojson"]
            )

        if status:
            status = subprocess.run(
                [
                    "tilesets",
                    "upload-source",
                    "--replace",
                    "go-ifrc",
                    centroids_tileset_source_name,
                    f"/tmp/{iso}-centroids.geojson",
                ]
            )

        return True if status.returncode == 0 else False

    def publish_admin2(self, iso, staging=True, create=False):
        if not create:
            update_status = self.update_admin2(iso, staging)
        else:
            update_status = True

        if update_status:
            polygon_tileset_name = f"go-ifrc.go-admin2-{iso}-staging"
            centroids_tileset_name = f"go-ifrc.go-admin2-{iso}-centroids"
            if not staging:
                polygon_tileset_name = f"go-ifrc.go-admin2-{iso}"

            publish_status = subprocess.run(["tilesets", "publish", polygon_tileset_name])
            publish_status = subprocess.run(["tilesets", "publish", centroids_tileset_name])
            return True if publish_status.returncode == 0 else False
        else:
            return False

    def prepare_admin2_geojson(self, iso):
        # query the database and create geojson
        try:
            os.remove(f"/tmp/{iso}.geojson")
        except FileNotFoundError:
            pass

        status = subprocess.run(
            [
                "ogr2ogr",
                "-f",
                "GeoJSON",
                f"/tmp/{iso}.geojson",
                self.connection_string,
                "-sql",
                f"select d.id as admin1_id, d.name as admin1_name, ad.name, ad.id, ad.code, adg.geom from api_country as c, api_district as d, api_admin2 as ad, api_admin2geoms as adg where c.id=d.country_id and c.iso3='{iso}' and ad.admin1_id=d.id and adg.admin2_id = ad.id",  # noqa: E501
            ]
        )
        if status:
            status = subprocess.run(
                [
                    "ogr2ogr",
                    "-f",
                    "GeoJSON",
                    f"/tmp/{iso}-centroids.geojson",
                    self.connection_string,
                    "-sql",
                    f"select d.id as admin1_id, d.name as admin1_name, ad.name, ad.id, ad.code, ad.centroid from api_country as c, api_district as d, api_admin2 as ad where c.id=d.country_id and c.iso3='{iso}' and ad.admin1_id=d.id",  # noqa: E501
                ]
            )

        return True if status.returncode == 0 else False
