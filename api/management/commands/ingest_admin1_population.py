import pandas as pd
from django.core.management.base import BaseCommand

from api.logger import logger
from api.models import Country, District


class Command(BaseCommand):
    help = "Population Data for District To run, python manage.py ingest_admin1_population Population.GO.Admin1.Matched.xlsx"

    def add_arguments(self, parser):
        parser.add_argument("filename", nargs="+", type=str)

    def handle(self, *args, **kwargs):
        logger.info("Updating population data for District")
        filename = kwargs["filename"][0]
        district_df = pd.read_excel(filename, usecols=["GO Names", "ISO3", "2016"])
        district_df = district_df.rename(columns={"GO Names": "District"})
        count = 0
        for index, row in district_df.iterrows():
            district = District.objects.filter(name=row["District"].strip(), country__iso3=row["ISO3"]).first()
            if district:
                count += 1
                district.wb_population = row["2016"]
                district.wb_year = "2016"  # Get this from excel file
                district.save(update_fields=["wb_population", "wb_year"])
        logger.info(f"Updated population data for {count} district")
