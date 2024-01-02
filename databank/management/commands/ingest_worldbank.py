import logging
import requests
from django.conf import settings
import datetime

from django.core.management.base import BaseCommand

from databank.models import CountryOverview as CO
from .sources.utils import catch_error, get_country_by_iso3
from api.models import Country

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Add Acaps seasonal calender data'

    def handle(self, *args, **kwargs):

        WORLD_BANK_INDICATOR_MAP = (
            ('SP.POP.TOTL', CO.world_bank_population),
            ('SP.POP.65UP.TO', CO.world_bank_population_above_age_65),
            ('SP.POP.0014.TO', CO.world_bank_population_age_14),
            ('SP.URB.TOTL.IN.ZS', CO.world_bank_urban_population_percentage),
            ('NY.GDP.MKTP.CD', CO.world_bank_gdp),
            ('NY.GNP.MKTP.CD', CO.world_bank_gni),
            ('IQ.CPA.GNDR.XQ', CO.world_bank_gender_inequality_index),
            ('SP.DYN.LE00.IN', CO.world_bank_life_expectancy),
            ('SE.ADT.LITR.ZS', CO.world_bank_literacy_rate),
        )

        WORLD_BANK_INDICATORS = [indicator for indicator, _ in WORLD_BANK_INDICATOR_MAP]
        data = {}

        #url = WORLD_BANK_API
        page = 1
        now = datetime.datetime.now()
        daterange = f'{now.year - 1}:{now.year}'
        while True:
            country_dict = {}
            for country_name in Country.objects.filter(iso3__isnull=False).values_list('iso3', flat=True):
                print(country_name, "@@@")
                for indicator in WORLD_BANK_INDICATORS:
                    rs = requests.get(f'https://api.worldbank.org/v2/country/{country_name}/indicator/{indicator}?date={daterange}', params={
                        'format': 'json',
                        'source': 2,
                        'per_page': 5000 - 1,  # WD throws error on 5000
                        'page': page,
                    })
                    rs.raise_for_status()
                    rs = rs.json()
                    print(rs)
                    #print(len(rs[1]))
                    if rs[1]:
                        print("@@@")
                        for pop_data in rs[1]:
                            #print(pop_data, "!!!!!!!")
                            geo_code = pop_data['countryiso3code']
                            pop = pop_data['value']
                            year = pop_data['date']
                            if len(geo_code) == 3:   # Admin Level 0
                                pcountry = get_country_by_iso3(geo_code)
                                if pcountry is None:
                                    continue
                                geo_id = pcountry.alpha_2
                                geo_id = geo_id.upper()

                                if data.get(geo_id) is None or data.get(geo_id)[1] < year:
                                    data[geo_id] = (pop, year, indicator)
                                    country_dict.update(data)
                                    print(country_dict, "~~~~~~~~")

                        if page >= rs[0]['pages']:
                            break
                        page += 1
                print(country_dict)
            return data, len(data)
