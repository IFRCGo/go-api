import datetime
import logging

import requests
from django.conf import settings

from api.models import Country
from databank.models import CountryOverview as CO

from .utils import catch_error, get_country_by_iso3

logger = logging.getLogger(__name__)


WORLD_BANK_INDICATOR_MAP = (
    ("SP.POP.TOTL", CO.world_bank_population),
    ("SP.POP.65UP.TO", CO.world_bank_population_above_age_65),
    ("SP.POP.0014.TO", CO.world_bank_population_age_14),
    ("SP.URB.TOTL.IN.ZS", CO.world_bank_urban_population_percentage),
    ("NY.GDP.MKTP.CD", CO.world_bank_gdp),
    ("NY.GNP.MKTP.CD", CO.world_bank_gni),
    ("IQ.CPA.GNDR.XQ", CO.world_bank_gender_inequality_index),
    ("SP.DYN.LE00.IN", CO.world_bank_life_expectancy),
    ("SE.ADT.LITR.ZS", CO.world_bank_literacy_rate),
)

WORLD_BANK_INDICATORS = [indicator for indicator, _ in WORLD_BANK_INDICATOR_MAP]

WORLD_BANK_API = ""


@catch_error()
def prefetch():
    data = {}

    url = WORLD_BANK_API
    page = 1
    now = datetime.datetime.now()
    daterange = f"{now.year - 1}:{now.year}"
    while True:
        for country_name in Country.objects.values_list("iso3", flat=True):
            for indicator in WORLD_BANK_INDICATORS:
                print(indicator)
                rs = requests.get(
                    f"https://api.worldbank.org/v2/country/{country_name}/indicator/{indicator}?date={daterange}",
                    params={
                        "format": "json",
                        "source": 2,
                        "per_page": 5000 - 1,  # WD throws error on 5000
                        "page": page,
                    },
                )
                rs.raise_for_status()
                rs = rs.json()
                print(rs)
                for pop_data in rs[1]:
                    # print(pop_data, "!!!!!!!")
                    geo_code = pop_data["countryiso3code"]
                    pop = pop_data["value"]
                    year = pop_data["date"]
                    if len(geo_code) == 3:  # Admin Level 0
                        pcountry = get_country_by_iso3(geo_code)
                        if pcountry is None:
                            continue
                        geo_id = pcountry.alpha_2
                        geo_id = geo_id.upper()

                        if data.get(geo_id) is None or data.get(geo_id)[1] < year:
                            data[geo_id] = (pop, year, indicator)

                if page >= rs[0]["pages"]:
                    break
                page += 1
                print(data)
        return data, len(data), WORLD_BANK_API


@catch_error()
def load(country, overview, wd_data):
    if not country.iso or wd_data is None:
        return

    pop, year = wd_data.get(country.iso.upper()) or (None, None)
    if pop is None:
        return
    country.wb_population = pop
    country.wb_year = year
    country.save(update_fields=["wb_population", "wb_year"])
