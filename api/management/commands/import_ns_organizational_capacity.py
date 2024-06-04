import csv

import pandas as pd
from django.core.management.base import BaseCommand, CommandError

from api.models import Country, CountryOrganizationalCapacity


class Command(BaseCommand):
    help = "import fdrs code for countries based on iso2. To run, python manage.py import-fdrs iso-fdrs.csv"

    def add_arguments(self, parser):
        parser.add_argument("filename", nargs="+", type=str)

    def update_or_create_capacity(self, sheet_name, field_mapping, filename):
        df_CAP = pd.read_excel(filename, sheet_name=sheet_name, usecols=["Country"] + list(field_mapping.keys()))
        CAP = df_CAP.dropna()

        for data in CAP.itertuples(index=False):
            country_name = data.Country.strip()
            country = CountryOrganizationalCapacity.objects.filter(country__name__icontains=country_name).first()

            if country:
                for excel_field, model_field in field_mapping.items():
                    setattr(country, model_field, data._asdict()[excel_field])
                country.save(update_fields=list(field_mapping.values()))
            else:
                country_id = Country.objects.filter(name__icontains=country_name).first()
                if country_id:
                    fields_to_create = {
                        model_field: data._asdict()[excel_field] for excel_field, model_field in field_mapping.items()
                    }
                    CountryOrganizationalCapacity.objects.create(country=country_id, **fields_to_create)

    def handle(self, *args, **options):
        leadership_mapping = {"LD_CAP": "leadership_capacity"}
        youth_mapping = {"Youth_CAP": "youth_capacity"}
        fd_mapping = {"FD_CAP": "financial_capacity"}
        volunteer_mapping = {"VD_CAP": "volunteer_capacity"}

        self.update_or_create_capacity("Leadership_CAP", leadership_mapping, options["filename"][0])
        self.update_or_create_capacity("Youth_CAP", youth_mapping, options["filename"][0])
        self.update_or_create_capacity("FD_CAP", fd_mapping, options["filename"][0])
        self.update_or_create_capacity("Volunteer_CAP", volunteer_mapping, options["filename"][0])
