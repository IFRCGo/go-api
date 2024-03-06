import logging
import requests

from django.conf import settings
from django.core.management.base import BaseCommand

from databank.models import CountryOverview, FDRSIncome
#from .utils import catch_error

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import FDRS income data'

    def handle(self, *args, **kwargs):

        FDRS_INDICATORS = [e.value for e in FDRSIncome.FDRSIndicator]

        for overview in CountryOverview.objects.all():
            country_fdrs_code = overview.country.fdrs
            FDRS_DATA_API_ENDPOINT = f'https://data-api.ifrc.org/api/data?apiKey={settings.FDRS_APIKEY}&KPI_Don_Code={country_fdrs_code}&indicator=' + ','.join(FDRS_INDICATORS)
            #@catch_error('Error occured while fetching from FDRS API.')
            fdrs_entities = requests.get(FDRS_DATA_API_ENDPOINT)
            if fdrs_entities.status_code != 200:
                return
            fdrs_entities.raise_for_status()
            fdrs_entities = fdrs_entities.json()
            for d in fdrs_entities['data']:
                indicator = next(iter(d.values()))
                income_list = d['data'][0]['data']
                if len(income_list):
                    for income in income_list:
                        data = {
                            'date': str(income['year']) + '-01-01',
                            'value': income['value'],
                            'indicator': indicator,
                            'overview': overview
                        }
                        FDRSIncome.objects.create(**data)
