import logging
import json
import requests
from django.core.management.base import BaseCommand
from api.models import Country, CountryType
from collections import defaultdict
from databank.models import CountryKeyClimate, CountryOverview
from datetime import datetime

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Add minimum, maximum and Average temperature of country temperature data from source api'


    def handle(self, *args, **options):
        for co in CountryOverview.objects.filter(country__record_type=CountryType.COUNTRY, country__iso3__isnull=False).all():
            country_iso3 = co.country.iso3
            if country_iso3:
                response = requests.get(f'https://climateknowledgeportal.worldbank.org/api/v1/cru-x0.5_climatology_tasmin,tas,tasmax,pr_climatology_monthly_1991-2020_mean_historical_cru_ts4.07_mean/{country_iso3}?_format=json')
                response.raise_for_status()
            try:
                response_data = response.json()
                data = response_data.get('data', {})
                if data:
                    precipation = data.get('pr', {})
                    average_temp = data.get('tas', {})
                    min_temp = data.get('tasmin', {})
                    max_temp = data.get('tasmax', {})
                    merged_data = {
                        country: {
                            date: (precipation[country][date], average_temp[country][date], min_temp[country][date], max_temp[country][date])
                            for date in precipation[country]
                        } for country in precipation
                    }
                    for key , value in merged_data.items():
                        for k, v in value.items():
                            year_month = k.split('-')
                            data = {
                                'year': year_month[0],
                                'month': year_month[1],
                                'max_temp' : v[3],
                                'min_temp' : v[2],
                                'avg_temp': v[1],
                                'precipitation' :v[0]
                            }
                            CountryKeyClimate.objects.create(
                                overview=co,
                                **data
                            )
            except Exception as ex:
                logger.error(f'Error in ingesting climate data',exc_info=True)
                continue