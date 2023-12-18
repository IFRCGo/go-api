import csv
import pandas as pd

from django.core.management.base import BaseCommand, CommandError

from api.models import Country, CountryOrganizationalCapacity


class Command(BaseCommand):
    help = "import fdrs code for countries based on iso2. To run, python manage.py import-fdrs iso-fdrs.csv"

    def add_arguments(self, parser):
        parser.add_argument("filename", nargs="+", type=str)

    #@transaction.atomic
    def handle(self, *args, **options):
        filename = options["filename"][0]
        df_LD_CAP = pd.read_excel(filename, sheet_name="Leadership_CAP", usecols=["Country", "LD_CAP"])
        LD_CAP = df_LD_CAP.dropna()
        for data in LD_CAP.values.tolist():
            country = CountryOrganizationalCapacity.objects.filter(
                country__name__icontains=data[0].strip()
            )
            if country.exists():
                country.first().leadership_capacity=[1]
                country.first().save(update_fields=['leadership_capacity'])
            else:
                country_id =Country.objects.filter(name__icontains=data[0].strip()).first()
                if country_id:
                    CountryOrganizationalCapacity.objects.create(
                        country=country_id,
                        leadership_capacity=data[1]
                    )

        df_Youth_CAP = pd.read_excel(filename, sheet_name="Youth_CAP", usecols=["Country", "Youth_CAP"])
        Youth_CAP = df_Youth_CAP.dropna()
        for data in Youth_CAP.values.tolist():
            country = CountryOrganizationalCapacity.objects.filter(
                country__name__icontains=data[0].strip()
            )
            if country.exists():
                country.first().youth_capacity=[1]
                country.first().save(update_fields=['youth_capacity'])
            else:
                country_id =Country.objects.filter(name__icontains=data[0].strip()).first()
                if country_id:
                    CountryOrganizationalCapacity.objects.create(
                        country=country_id,
                        youth_capacity=data[1]
                    )

        df_FD_CAP = pd.read_excel(filename, sheet_name="FD_CAP", usecols=["Country", "FD_CAP"])
        FD_CAP = df_FD_CAP.dropna()
        for data in FD_CAP.values.tolist():
            country = CountryOrganizationalCapacity.objects.filter(
                country__name__icontains=data[0].strip()
            )
            if country.exists():
                country.first().financial_capacity=[1]
                country.first().save(update_fields=['financial_capacity'])
            else:
                country_id =Country.objects.filter(name__icontains=data[0].strip()).first()
                if country_id:
                    CountryOrganizationalCapacity.objects.create(
                        country=country_id,
                        financial_capacity=data[1]
                    )

        df_Volunteer_Cap = pd.read_excel(filename, sheet_name="Volunteer_CAP", usecols=["Country", "VD_CAP"])
        Volunteer_Cap = df_Volunteer_Cap.dropna()
        for data in Volunteer_Cap.values.tolist():
            country = CountryOrganizationalCapacity.objects.filter(
                country__name__icontains=data[0].strip()
            )
            if country.exists():
                country.first().volunteer_capacity=[1]
                country.first().save(update_fields=['volunteer_capacity'])
            else:
                country_id = Country.objects.filter(name__icontains=data[0].strip()).first()
                if country_id:
                    CountryOrganizationalCapacity.objects.create(
                        country=country_id,
                        volunteer_capacity=data[1]
                    )
