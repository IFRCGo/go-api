import logging

import requests
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from sentry_sdk.crons import monitor

from databank.models import CountryOverview, FDRSIncome, FDRSIndicator
from main.sentry import SentryMonitor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import FDRS income data"

    @monitor(monitor_slug=SentryMonitor.FDRS_INCOME)
    def handle(self, *args, **kwargs):
        # NOTE: Loading FDRS indicators
        call_command("loaddata", "fdrs_indicator.json", verbosity=2)

        fdrs_indicator_enum_data = {
            "h_gov_CHF": "Home Government",
            "f_gov_CHF": "Foreign Government",
            "ind_CHF": "Individuals",
            "corp_CHF": "Corporations",
            "found_CHF": "Foundations",
            "un_CHF": "UN Agencies and other Multilateral Agencies",
            "pooled_f_CHF": "Pooled funds",
            "ngo_CHF": "Non-governmental organizations",
            "si_CHF": "Service income",
            "iga_CHF": "Income generating activity",
            "KPI_incomeFromNSsLC_CHF": "Other National Society",
            "ifrc_CHF": "IFRC (HQ, regional and countries delegations)",
            "icrc_CHF": "ICRC",
            "other_CHF": "Other",
        }
        FDRS_INDICATORS = [key for key in fdrs_indicator_enum_data]
        map_indicators = {indicator.title: indicator for indicator in FDRSIndicator.objects.all()}
        for overview in CountryOverview.objects.all():
            country_fdrs_code = overview.country.fdrs
            FDRS_DATA_API_ENDPOINT = (
                f"https://data-api.ifrc.org/api/data?apiKey={settings.FDRS_APIKEY}&KPI_Don_Code={country_fdrs_code}&indicator="
                + ",".join(FDRS_INDICATORS)
            )
            fdrs_entities = requests.get(FDRS_DATA_API_ENDPOINT)
            if fdrs_entities.status_code != 200:
                return
            fdrs_entities.raise_for_status()
            fdrs_entities = fdrs_entities.json()
            created_fdrs_income_ids = []
            with transaction.atomic():
                for d in fdrs_entities["data"]:
                    indicator = next(iter(d.values()))
                    fdrs_indicator = map_indicators[fdrs_indicator_enum_data[indicator]]
                    income_list = d["data"][0]["data"]
                    if len(income_list):
                        for income in income_list:
                            income_value = income["value"]
                            fdrs_income, created = FDRSIncome.objects.get_or_create(
                                overview=overview,
                                indicator=fdrs_indicator,
                                date=str(income["year"]) + "-01-01",
                                defaults={"value": income_value},
                            )
                            if not created:
                                fdrs_income.value = income_value
                                fdrs_income.save(update_fields=["value"])
                            created_fdrs_income_ids.append(fdrs_income.pk)
                # NOTE: Delete the FDRSIncome that are not in the source
                FDRSIncome.objects.filter(overview=overview).exclude(id__in=created_fdrs_income_ids).delete()
