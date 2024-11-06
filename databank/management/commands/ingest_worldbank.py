import datetime
import logging
import time
import typing

import requests
from django.core.management.base import BaseCommand
from django.db import models
from sentry_sdk.crons import monitor

from api.models import Country, CountryType
from databank.models import CountryOverview
from main.managers import BulkUpdateManager
from main.sentry import SentryMonitor
from main.utils import logger_context, pretty_seconds

logger = logging.getLogger(__name__)


class CountryIndicatorData(typing.TypedDict):
    year: int
    value: int


WORLD_BANK_INDICATOR_MAP = {
    "SP.POP.TOTL": (
        CountryOverview.world_bank_population,
        CountryOverview.world_bank_population_year,
    ),
    "SP.POP.65UP.TO": (
        CountryOverview.world_bank_population_above_age_65,
        CountryOverview.world_bank_population_above_age_65_year,
    ),
    "SP.POP.0014.TO": (
        CountryOverview.world_bank_population_age_14,
        CountryOverview.world_bank_population_age_14_year,
    ),
    "SP.URB.TOTL.IN.ZS": (
        CountryOverview.world_bank_urban_population_percentage,
        CountryOverview.world_bank_urban_population_percentage_year,
    ),
    "NY.GDP.MKTP.CD": (
        CountryOverview.world_bank_gdp,
        CountryOverview.world_bank_gdp_year,
    ),
    "NY.GNP.MKTP.CD": (
        CountryOverview.world_bank_gni,
        CountryOverview.world_bank_gni_year,
    ),
    "IQ.CPA.GNDR.XQ": (
        CountryOverview.world_bank_gender_equality_index,
        CountryOverview.world_bank_gender_equality_index_year,
    ),
    "SP.DYN.LE00.IN": (
        CountryOverview.world_bank_life_expectancy,
        CountryOverview.world_bank_life_expectancy_year,
    ),
    "SE.ADT.LITR.ZS": (
        CountryOverview.world_bank_literacy_rate,
        CountryOverview.world_bank_literacy_rate_year,
    ),
    "SI.POV.NAHC": (
        CountryOverview.world_bank_poverty_rate,
        CountryOverview.world_bank_poverty_rate_year,
    ),
    "NY.GNP.PCAP.CD": (
        CountryOverview.world_bank_gni_capita,
        CountryOverview.world_bank_gni_capita_year,
    ),
}

COUNTRY_OVERVIEW_CHANGED_FIELDS = [field.field.name for fields in WORLD_BANK_INDICATOR_MAP.values() for field in fields]


class Command(BaseCommand):
    help = "Ingest worldbank indicators data"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # NOTE: With session, connection are re-used
        self.requests = requests.session()

    def show_stats(self, country_qs):
        self.stdout.write("Countries with empty data per indicators?")
        for indicator, (value_field, year_field) in WORLD_BANK_INDICATOR_MAP.items():
            count = CountryOverview.objects.filter(
                models.Q(
                    **{
                        f"{value_field.field.name}__isnull": True,
                    }
                )
                | models.Q(
                    **{
                        f"{year_field.field.name}__isnull": True,
                    }
                ),
                country__in=country_qs.values("id"),
            ).count()
            if count > 0:
                self.stdout.write(self.style.WARNING(f" - {indicator:<20}: {count}"))

    @staticmethod
    def get_date_range(start_year: int, end_year: int):
        return f"{start_year}:{end_year}"  # Fetch data up to 10 years.

    def paginated_response(self, iso3, indicator, daterange) -> typing.Iterator[dict]:
        """
        This adds support for pagination.
        NOTE: With current per_page 5000 -1, pagination is called rarely
        """
        page = 1
        while True:

            response = self.requests.get(
                f"https://api.worldbank.org/v2/country/{iso3}/indicator/{indicator}",
                params={
                    "date": daterange,
                    "format": "json",
                    "source": 2,
                    "per_page": 5000 - 1,  # World Bank throws error on 5000
                    "page": page,
                },
            )

            error_context = logger_context(
                {
                    "url": response.url,
                    "content": response.content,
                }
            )

            if response.status_code != 200:
                logger.error("Worldbank ingest: Failed to fetch data", extra=error_context)
                break

            response_json = response.json()
            if not isinstance(response_json, list) or len(response_json) != 2:
                logger.error("Worldbank ingest: Unexpected response from endpoint", extra=error_context)
                break

            response_meta, response_data = response_json
            for item in response_data or []:
                yield item

            response_page = response_meta["pages"]
            if page >= response_page:
                break
            page += 1

    @monitor(monitor_slug=SentryMonitor.INGEST_WORLDBANK)
    def handle(self, **_):
        bulk_mgr = BulkUpdateManager(update_fields=COUNTRY_OVERVIEW_CHANGED_FIELDS, chunk_size=20)
        total_start_time = time.time()
        now = datetime.datetime.now()
        default_daterange = self.get_date_range(now.year - 10, now.year)

        country_qs = (
            Country.objects.filter(
                iso3__isnull=False,
                record_type=CountryType.COUNTRY,
                region__isnull=False,
                independent=True,
            )
            .select_related("countryoverview")
            .exclude(iso3__in=["COK", "BAR", "NOR"])
        )

        total_countries = country_qs.count()
        for index, country in enumerate(country_qs, start=1):
            iso3 = country.iso3
            self.stdout.write(f"Importing country ({index:03}/{total_countries}): {iso3}")
            overview = CountryOverview(country=country)

            # Pre-fetch to generate smaller date-range relative to local
            indicator_data: dict[str, CountryIndicatorData] = {
                indicator: CountryIndicatorData(
                    value=getattr(overview, value_field.field.name),
                    year=int(getattr(overview, year_field.field.name)),
                )
                for indicator, (value_field, year_field) in WORLD_BANK_INDICATOR_MAP.items()
                if not (getattr(overview, year_field.field.name) is None or getattr(overview, value_field.field.name) is None)
            }

            for indicator in WORLD_BANK_INDICATOR_MAP.keys():
                daterange = default_daterange
                if indicator in indicator_data:
                    # XXX: This is a simple check to avoid using invalid year. We can remove this later
                    if (now.year - 10) <= indicator_data[indicator]["year"] <= now.year:
                        # Avoid historical data we have already processed
                        daterange = self.get_date_range(indicator_data[indicator]["year"], now.year)

                for data in self.paginated_response(iso3, indicator, daterange):
                    value = data["value"]
                    year = int(data["date"])

                    if value is None:
                        continue

                    if indicator not in indicator_data or year >= indicator_data[indicator]["year"]:
                        indicator_data[indicator] = CountryIndicatorData(
                            year=year,
                            value=value,
                        )

                if indicator not in indicator_data:
                    # There was no data available in remote
                    continue

                # Set the latest data to the fields
                setattr(overview, WORLD_BANK_INDICATOR_MAP[indicator][0].field.name, indicator_data[indicator]["value"])
                setattr(
                    overview,
                    WORLD_BANK_INDICATOR_MAP[indicator][1].field.name,
                    indicator_data[indicator]["year"],
                )

            # Save the country overview
            bulk_mgr.add(overview)
        self.stdout.write(f"Total Runtime: {pretty_seconds(time.time() - total_start_time)}")

        bulk_mgr.done()
        self.stdout.write(self.style.SUCCESS(f"Updated: {bulk_mgr.summary()}"))

        self.show_stats(country_qs)
