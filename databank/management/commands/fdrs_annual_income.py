import logging

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import models, transaction
from sentry_sdk.crons import monitor

from databank.models import CountryOverview, FDRSAnnualIncome
from main.sentry import SentryMonitor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import FDRS income data"

    @monitor(monitor_slug=SentryMonitor.FDRS_ANNUAL_INCOME)
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

            created_fdrs_income_ids = []
            with transaction.atomic():
                for income in income_list:
                    income_value = income["value"]
                    fdrs_annual_income, created = FDRSAnnualIncome.objects.get_or_create(
                        overview=overview,
                        date=str(income["year"]) + "-01-01",
                        defaults={"value": income_value},
                    )
                    if not created:
                        fdrs_annual_income.value = income_value
                        fdrs_annual_income.save(update_fields=["value"])
                    created_fdrs_income_ids.append(fdrs_annual_income.pk)
                    fdrs_data_count += 1
                # NOTE: Deleting the FDRSAnnualIncome objects that are not in the source
                FDRSAnnualIncome.objects.filter(overview=overview).exclude(id__in=created_fdrs_income_ids).delete()
        logger.info(f"Successfully created {fdrs_data_count} country data")
