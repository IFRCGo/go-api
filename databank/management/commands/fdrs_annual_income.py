import logging

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import models
from sentry_sdk.crons import monitor

from databank.models import CountryOverview, FDRSAnnualIncome
from main.sentry import SentryMonitor

logger = logging.getLogger(__name__)


@monitor(monitor_slug=SentryMonitor.FDRS_ANNUAL_INCOME)
class Command(BaseCommand):
    help = "Import FDRS income data"

    def handle(self, *args, **kwargs):
        overview_qs = CountryOverview.objects.annotate(
            country_fdrd=models.F("country__fdrs"),
        )
        fdrs_data_count = 0
        for overview in overview_qs.all():
            country_fdrs_code = overview.country_fdrd
            fdrs_entities = requests.get(
                "https://data-api.ifrc.org/api/data",
                params={
                    "apiKey": settings.FDRS_APIKEY,
                    "indicator": "KPI_IncomeLC_CHF",
                    "KPI_Don_Code": country_fdrs_code,
                },
            )
            if fdrs_entities.status_code != 200:
                continue

            fdrs_entities.raise_for_status()
            fdrs_entities = fdrs_entities.json()

            if len(fdrs_entities["data"]) == 0:
                continue

            income_list = fdrs_entities["data"][0]["data"][0]["data"]
            if len(income_list) == 0:
                continue

            for income in income_list:
                income_value = income["value"]
                fdrs_annual_income, _ = FDRSAnnualIncome.objects.get_or_create(
                    overview=overview,
                    date=str(income["year"]) + "-01-01",
                )
                fdrs_annual_income.value = income_value
                fdrs_annual_income.save(update_fields=("value",))
                fdrs_data_count += 1

        logger.info(f"Successfully created {fdrs_data_count} country data")
