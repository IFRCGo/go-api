import logging

import requests
from django.core.management.base import BaseCommand
from django.db import models
from sentry_sdk.crons import monitor

from api.models import CountryType
from databank.models import CountryKeyClimate, CountryOverview
from main.sentry import SentryMonitor

logger = logging.getLogger(__name__)


@monitor(monitor_slug=SentryMonitor.INGEST_CLIMATE)
class Command(BaseCommand):
    help = "Add minimum, maximum and Average temperature of country temperature data from source api"

    def handle(self, *args, **options):
        overview_qs = CountryOverview.objects.filter(
            country__record_type=CountryType.COUNTRY,
            country__iso3__isnull=False,
        ).annotate(
            country_iso3=models.F("country__iso3"),
        )

        for overview in overview_qs.all():
            country_iso3 = overview.country_iso3
            if not country_iso3:
                continue

            response = requests.get(
                f"https://climateknowledgeportal.worldbank.org/api/v1/cru-x0.5_climatology_tasmin,tas,tasmax,pr_climatology_monthly_1991-2020_mean_historical_cru_ts4.07_mean/{country_iso3}?_format=json"  # noqa: E501
            )

            try:
                response.raise_for_status()
                response_data = response.json()
                data = response_data.get("data", {})
                if not data:
                    continue

                precipitation = data.get("pr", {})
                average_temp = data.get("tas", {})
                min_temp = data.get("tasmin", {})
                max_temp = data.get("tasmax", {})
                merged_data = {
                    country: {
                        date: (
                            precipitation[country][date],
                            average_temp[country][date],
                            min_temp[country][date],
                            max_temp[country][date],
                        )
                        for date in precipitation[country]
                    }
                    for country in precipitation
                }

                for value in merged_data.values():
                    for k, v in value.items():
                        year_month = k.split("-")
                        country_key_climate, _ = CountryKeyClimate.objects.get_or_create(
                            overview=overview,
                            year=year_month[0],
                            month=year_month[1],
                        )
                        country_key_climate.max_temp = v[3]
                        country_key_climate.min_temp = v[2]
                        country_key_climate.avg_temp = v[1]
                        country_key_climate.precipitation = v[0]
                        # TODO: Use bulk manager
                        country_key_climate.save(
                            update_fields=(
                                "max_temp",
                                "min_temp",
                                "avg_temp",
                                "precipitation",
                            )
                        )
            except Exception:
                logger.error("Error in ingesting climate data", exc_info=True)
                continue
