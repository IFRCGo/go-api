import logging
import requests

from django.conf import settings
from django.core.management.base import BaseCommand

from databank.models import (
    CountryOverview,
    FDRSIncome,
    FDRSIndicator
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import FDRS income data'

    def handle(self, *args, **kwargs):
        fdrs_indicator_enum_data = {
            "h_gov_CHF": "Home Government",
            "f_gov_CHF": "Foreign Government",
            "ind_CHF": "Individuals",
            "corp_CHF": "Corporations",
            "found_CHF": "Foundations",
            "un_CHF": "UN Agencies and other Multilateral Agencies",
            "pooled_f_CHF": "Pooled funds",
            "ngo_CHF": "Non-governmental organizations",
            "si_CHF": "Service income",
            "iga_CHF": "Income generating activity",
            "KPI_incomeFromNSsLC_CHF": "Other National Society",
            "ifrc_CHF": "IFRC (HQ, regional and countries delegations)",
            "icrc_CHF": "ICRC",
            "other_CHF": "Other",
        }
        FDRS_INDICATORS = [key for key in fdrs_indicator_enum_data]
        map_indicators = {
            indicator.title: indicator
            for indicator in FDRSIndicator.objects.all()
        }
        for overview in CountryOverview.objects.all():
            country_fdrs_code = overview.country.fdrs
            FDRS_DATA_API_ENDPOINT = f'https://data-api.ifrc.org/api/data?apiKey={settings.FDRS_APIKEY}&KPI_Don_Code={country_fdrs_code}&indicator=' + ','.join(FDRS_INDICATORS)
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
                            'indicator': map_indicators.get(fdrs_indicator_enum_data.get(indicator)),
                            'overview': overview
                        }
                        FDRSIncome.objects.create(**data)
