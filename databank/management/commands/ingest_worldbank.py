import logging
import requests
from django.core.management.base import BaseCommand
from databank.models import CountryOverview as CO
from .sources.utils import catch_error, get_country_by_iso3
from api.models import Country, CountryType
import datetime
import json

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Add Acaps seasonal calendar data'

    def handle(self, *args, **kwargs):
        world_bank_indicator_map = (
            ('SP.POP.TOTL', CO.world_bank_population),
            ('SP.POP.65UP.TO', CO.world_bank_population_above_age_65),
            ('SP.POP.0014.TO', CO.world_bank_population_age_14),
            ('SP.URB.TOTL.IN.ZS', CO.world_bank_urban_population_percentage),
            ('NY.GDP.MKTP.CD', CO.world_bank_gdp),
            ('NY.GNP.MKTP.CD', CO.world_bank_gni),
            ('IQ.CPA.GNDR.XQ', CO.world_bank_gender_inequality_index),
            ('SP.DYN.LE00.IN', CO.world_bank_life_expectancy),
            ('SE.ADT.LITR.ZS', CO.world_bank_literacy_rate),
            ('SI.POV.NAHC', CO.world_bank_poverty_rate)
        )

        world_bank_indicators = [indicator for indicator, _ in world_bank_indicator_map]
        country_dict = {}

        now = datetime.datetime.now()
        daterange = f'{now.year - 1}:{now.year}'

        for country in Country.objects.filter(
            iso3__isnull=False,
            record_type=CountryType.COUNTRY,
            region__isnull=False,
            independent=True
        ).exclude(iso3="COK"):
            country_iso3 = country.iso3
            logger.info(f'Importing country {country_iso3}')
            for indicator in world_bank_indicators:
                page = 1  # Reset the page for each indicator
                while True:
                    try:
                        response = requests.get(f'https://api.worldbank.org/v2/country/{country_iso3}/indicator/{indicator}?date={daterange}', params={
                        'format': 'json',
                        'source': 2,
                        'per_page': 5000 - 1,  # World Bank throws error on 5000
                        'page': page,
                        })
                    except requests.exceptions.HTTPError as err:
                        continue
                    try:
                        data_list = response.json()[1]
                        if data_list is not None and len(data_list) > 0:
                            data = data_list
                    except (IndexError, KeyError):
                        continue
                    if data:
                        # Check if data_list is not None and has elements
                        for pop_data in data:
                            geo_code = pop_data['countryiso3code']
                            pop = pop_data['value']
                            year = pop_data['date']

                            if len(geo_code) == 3:
                                pcountry = get_country_by_iso3(geo_code)
                                if pcountry is not None:
                                    geo_id = pcountry.alpha_2.upper()

                                    if geo_id not in country_dict:
                                        country_dict[geo_id] = []
                                    existing_data = next((data for data in country_dict[geo_id] if data[2] == indicator), None)
                                    if existing_data is None or existing_data[1] < year:
                                        country_dict[geo_id].append((pop, year, indicator))
                                        logger.info(json.dumps(country_dict))
                        if 'pages' in response.json()[0]:
                            if page >= response.json()[0]['pages']:
                                break
                        page += 1

        for country_code, indicators in country_dict.items():
            overview = CO.objects.filter(country__iso=country_code).first()
            if overview:
                overview.world_bank_population = indicators[0][0]
                overview.world_bank_population_above_age_65 = indicators[1][0]
                overview.world_bank_population_age_14 = indicators[2][0]
                overview.world_bank_urban_population_percentage = indicators[3][0]
                overview.world_bank_gdp = indicators[4][0]
                overview.world_bank_gni = indicators[5][0]
                overview.world_bank_gender_inequality_index = indicators[6][0]
                overview.world_bank_life_expectancy = indicators[7][0]
                overview.world_bank_literacy_rate = indicators[8][0]
                overview.world_bank_poverty_rate = indicators[9][0]
                overview.save(
                    update_fields=[
                        'world_bank_population',
                        'world_bank_population_above_age_65',
                        'world_bank_population_age_14',
                        'world_bank_urban_population_percentage',
                        'world_bank_gdp',
                        'world_bank_gni',
                        'world_bank_gender_inequality_index',
                        'world_bank_life_expectancy',
                        'world_bank_literacy_rate',
                        'world_bank_poverty_rate'
                    ]
                )
