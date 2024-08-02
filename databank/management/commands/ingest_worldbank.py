import datetime
import json
import logging

import requests
from django.core.management.base import BaseCommand
from sentry_sdk.crons import monitor

from api.models import Country, CountryType
from databank.models import CountryOverview as CO
from main.sentry import SentryMonitor

from .sources.utils import get_country_by_iso3

logger = logging.getLogger(__name__)


def get_indicator_value(indicator):
    try:
        result = indicator[0]
    except (IndexError, TypeError):
        result = None
    return result


def get_indicator_year(indicator):
    try:
        result = indicator[1]
    except (IndexError, TypeError):
        result = None
    return result


class Command(BaseCommand):
    help = "Add Acaps seasonal calendar data"

    @monitor(monitor_slug=SentryMonitor.INGEST_WORLDBANK)
    def handle(self, *args, **kwargs):
        world_bank_indicator_map = (
            ("SP.POP.TOTL", CO.world_bank_population),
            ("SP.POP.65UP.TO", CO.world_bank_population_above_age_65),
            ("SP.POP.0014.TO", CO.world_bank_population_age_14),
            ("SP.URB.TOTL.IN.ZS", CO.world_bank_urban_population_percentage),
            ("NY.GDP.MKTP.CD", CO.world_bank_gdp),
            ("NY.GNP.MKTP.CD", CO.world_bank_gni),
            ("IQ.CPA.GNDR.XQ", CO.world_bank_gender_inequality_index),
            ("SP.DYN.LE00.IN", CO.world_bank_life_expectancy),
            ("SE.ADT.LITR.ZS", CO.world_bank_literacy_rate),
            ("SI.POV.NAHC", CO.world_bank_poverty_rate),
            ("NY.GNP.PCAP.CD", CO.world_bank_gni_capita),
        )

        world_bank_indicators = [indicator for indicator, _ in world_bank_indicator_map]
        country_dict = {}

        now = datetime.datetime.now()
        daterange = f"{now.year - 10}:{now.year}"  # Fetch data up to 10 years.

        for country in Country.objects.filter(
            iso3__isnull=False, record_type=CountryType.COUNTRY, region__isnull=False, independent=True
        ).exclude(iso3__in=["COK", "BAR", "NOR"]):
            country_iso3 = country.iso3
            print(f"Importing country {country_iso3}")
            for indicator in world_bank_indicators:
                page = 1  # Reset the page for each indicator
                while True:
                    try:
                        response = requests.get(
                            f"https://api.worldbank.org/v2/country/{country_iso3}/indicator/{indicator}?date={daterange}",
                            params={
                                "format": "json",
                                "source": 2,
                                "per_page": 5000 - 1,  # World Bank throws error on 5000
                                "page": page,
                            },
                        )
                        response.raise_for_status()
                    except requests.exceptions.HTTPError:
                        continue

                    try:
                        data_list = response.json()[1]
                        if data_list is not None and len(data_list) > 0:
                            data = data_list
                    except (IndexError, KeyError):
                        continue

                    if data:
                        country_data = None
                        geo_id = None
                        existing_data = None
                        for datum in data:
                            geo_code = datum["countryiso3code"]
                            value = datum["value"]
                            year = datum["date"]

                            if len(geo_code) == 3:
                                pcountry = get_country_by_iso3(geo_code)
                                if pcountry is not None:
                                    geo_id = pcountry.alpha_2.upper()

                                    if geo_id not in country_dict:
                                        country_dict[geo_id] = []

                                    if value is not None:
                                        if existing_data is None or year > existing_data["date"]:
                                            existing_data = datum
                                            country_data = (value, year, indicator)
                        country_dict[geo_id].append(country_data)
                        logger.info(json.dumps(country_dict))

                        if "pages" in response.json()[0]:
                            if page >= response.json()[0]["pages"]:
                                break
                        page += 1

        for country_code, indicators in country_dict.items():
            overview = CO.objects.filter(country__iso=country_code).first()
            if overview:
                overview.world_bank_population = get_indicator_value(indicators[0])
                overview.calculated_world_bank_population_year = get_indicator_year(indicators[0])

                overview.world_bank_population_above_age_65 = get_indicator_value(indicators[1])
                overview.calculated_world_bank_population_above_age_65_year = get_indicator_year(indicators[1])

                overview.world_bank_population_age_14 = get_indicator_value(indicators[2])
                overview.calculated_world_bank_population_age_14_year = get_indicator_year(indicators[2])

                overview.world_bank_urban_population_percentage = get_indicator_value(indicators[3])
                overview.calculated_world_bank_urban_population_percentage_year = get_indicator_year(indicators[3])

                overview.world_bank_gdp = get_indicator_value(indicators[4])
                overview.calculated_world_bank_gdp_year = get_indicator_year(indicators[4])

                overview.world_bank_gni = get_indicator_value(indicators[5])
                overview.calculated_world_bank_gni_year = get_indicator_year(indicators[5])

                overview.world_bank_gender_inequality_index = get_indicator_value(indicators[6])
                overview.calculated_world_bank_gender_inequality_index_year = get_indicator_year(indicators[6])

                overview.world_bank_life_expectancy = get_indicator_value(indicators[7])
                overview.calculated_world_bank_life_expectancy_year = get_indicator_year(indicators[7])

                overview.world_bank_literacy_rate = get_indicator_value(indicators[8])
                overview.calculated_world_bank_literacy_rate_year = get_indicator_year(indicators[8])

                overview.world_bank_poverty_rate = get_indicator_value(indicators[9])
                overview.calculated_world_bank_poverty_rate_year = get_indicator_year(indicators[9])

                overview.world_bank_gni_capita = get_indicator_value(indicators[10])
                overview.calculated_world_bank_gni_capita_year = get_indicator_value(indicators[10])
                overview.save(
                    update_fields=[
                        "world_bank_population",
                        "calculated_world_bank_population_year",
                        "world_bank_population_above_age_65",
                        "calculated_world_bank_population_above_age_65_year",
                        "world_bank_population_age_14",
                        "calculated_world_bank_population_age_14_year",
                        "world_bank_urban_population_percentage",
                        "calculated_world_bank_urban_population_percentage_year",
                        "world_bank_gdp",
                        "calculated_world_bank_gdp_year",
                        "world_bank_gni",
                        "calculated_world_bank_gni_year",
                        "world_bank_gender_inequality_index",
                        "calculated_world_bank_gender_inequality_index_year",
                        "world_bank_life_expectancy",
                        "calculated_world_bank_life_expectancy_year",
                        "world_bank_literacy_rate",
                        "calculated_world_bank_literacy_rate_year",
                        "world_bank_poverty_rate",
                        "calculated_world_bank_poverty_rate_year",
                        "world_bank_gni_capita",
                        "calculated_world_bank_gni_capita_year",
                    ]
                )
