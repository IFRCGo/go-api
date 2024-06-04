import geopandas as gpd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Converting Shapefiles from different sources to custom file for go-api. To run, python manage.py generate-admin2-shp input.shp output.shp --source=fews"

    missing_args_message = "Filename is missing. A shapefile with valid admin polygons is required."

    def add_arguments(self, parser):
        parser.add_argument("filename", nargs="+", type=str)
        parser.add_argument("--source", help="Shapefile source, Can be : gadm or fews")

    @transaction.atomic
    def handle(self, *args, **options):
        input_filename = options["filename"][0]
        output_filename = options["filename"][1]
        try:
            gdf = gpd.read_file(input_filename)
        except:
            raise CommandError("Could not open file")
        if options["source"] == "fews":
            gdf.rename(columns={"shapeName": "name"}, inplace=True)
            gdf.rename(columns={"shapeID": "code"}, inplace=True)
        if options["source"] == "gadm":
            gdf.rename(columns={"NAME_2": "name"}, inplace=True)
            gdf.rename(columns={"GID_2": "code"}, inplace=True)
        gdf.to_file(output_filename)
