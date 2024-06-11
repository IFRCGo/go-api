import logging

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from databank.models import CountryOverview, FDRSAnnualIncome

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import FDRS income data"

    def handle(self, *args, **kwargs):
        for overview in CountryOverview.objects.all():
            country_fdrs_code = overview.country.fdrs
            fdrs_api = f"https://data-api.ifrc.org/api/data?indicator=KPI_IncomeLC_CHF&KPI_Don_Code={country_fdrs_code}&apiKey={settings.FDRS_APIKEY}"  # noqa: E501
            fdrs_entities = requests.get(fdrs_api)
            if fdrs_entities.status_code != 200:
                return
            fdrs_entities.raise_for_status()
            fdrs_entities = fdrs_entities.json()
            fdrs_data_count = 0
            if len(fdrs_entities["data"]):
                income_list = fdrs_entities["data"][0]["data"][0]["data"]
                if len(income_list):
                    for income in income_list:
                        data = {"date": str(income["year"]) + "-01-01", "value": income["value"], "overview": overview}
                        fdrs_data_count += 1
                        FDRSAnnualIncome.objects.get_or_create(**data)
        logger.info(f"Successfully created {fdrs_data_count} country data")
