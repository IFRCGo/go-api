import logging

import requests
from django.core.management.base import BaseCommand
from django.db import models, transaction
from sentry_sdk.crons import monitor

from api.models import CountryType
from databank.models import CountryKeyClimate, CountryOverview
from main.sentry import SentryMonitor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Add minimum, maximum and Average temperature of country temperature data from source api"

    @monitor(monitor_slug=SentryMonitor.INGEST_CLIMATE)
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
                    date: {
                        "precipitation": precipitation[country][date],
                        "average_temp": average_temp[country][date],
                        "min_temp": min_temp[country][date],
                        "max_temp": max_temp[country][date],
                    }
                    for date in precipitation[country]
                }
                for country in precipitation
            }
            created_country_key_climate_ids = []
            with transaction.atomic():
                for value in merged_data.values():
                    for k, v in value.items():
                        if (
                            v["precipitation"] is None
                            or v["average_temp"] is None
                            or v["min_temp"] is None
                            or v["max_temp"] is None
                        ):
                            continue
                        year_month = k.split("-")
                        country_key_climate, created = CountryKeyClimate.objects.get_or_create(
                            overview=overview,
                            year=year_month[0],
                            month=year_month[1],
                            defaults={
                                "precipitation": v["precipitation"],
                                "avg_temp": v["average_temp"],
                                "min_temp": v["min_temp"],
                                "max_temp": v["max_temp"],
                            },
                        )
                        if not created:
                            country_key_climate.precipitation = v.get("precipitation")
                            country_key_climate.avg_temp = v.get("average_temp")
                            country_key_climate.min_temp = v.get("min_temp")
                            country_key_climate.max_temp = v.get("max_temp")
                            country_key_climate.save(update_fields=["precipitation", "avg_temp", "min_temp", "max_temp"])
                        created_country_key_climate_ids.append(country_key_climate.pk)
                # NOTE: Deleting the CountryKeyclimate that are not in the source
                CountryKeyClimate.objects.filter(overview=overview).exclude(id__in=created_country_key_climate_ids).delete()
