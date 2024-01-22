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

        FDRS_NS_API_ENDPOINT = f'https://data-api.ifrc.org/api/entities/ns?apiKey={settings.FDRS_APIKEY}'

        # To fetch NS Data using NS ID
        FDRS_DATA_API_ENDPOINT = f'https://data-api.ifrc.org/api/data?apiKey={settings.FDRS_APIKEY}&indicator=' + ','.join(FDRS_INDICATORS)


        #@catch_error('Error occured while fetching from FDRS API.')
        fdrs_entities = requests.get(FDRS_NS_API_ENDPOINT)
        if fdrs_entities.status_code != 200:
            return
        fdrs_entities.raise_for_status()
        fdrs_entities = fdrs_entities.json()

        ns_iso_map = {
            # ISO3 are missing for some in FDRS & IFRC-GO only have ISO2 for countries
            ns['KPI_DON_code']: ns['iso_2']
            for ns in fdrs_entities
        }

        data =  {
            # KEY <ISO2>-<Indicator_ID>: {year: '', value: ''}
            f"{ns_iso_map[ns_data['id']].upper()}-{indicator_data['id']}": (
                ns_data['data'][-1] if (
                    ns_data['data'] and len(ns_data['data']) > 0
                ) else None
            )
            for indicator_data in requests.get(FDRS_DATA_API_ENDPOINT).json()['data']
            for ns_data in indicator_data['data']
        }
        for key, value in data.items():
            country_indicator = key.split('-')
            country_iso = country_indicator[0]
            indicator = country_indicator[1]
            if value and len(value) > 0:
                year = str(value['year']) + '-01-01'
                value = value['value']
                data = {
                    'overview' : CountryOverview.objects.filter(country__iso=country_iso).first(),
                    'date' : year,
                    'indicator' : indicator,
                    'value': value,
                }
                FDRSIncome.objects.create(**data)
