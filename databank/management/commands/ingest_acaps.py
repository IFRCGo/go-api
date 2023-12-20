import requests
import datetime as dt
import xmltodict
import pandas as pd
from dateutil.parser import parse

from django.core.management.base import BaseCommand

from api.models import Country, CountryType, CronJob, CronJobStatus, DisasterType
from api.logger import logger
from databank.models import CountryOverview, AcapsSeasonalCalender


class Command(BaseCommand):
    help = 'Add Acaps seasonal calender data'

    def handle(self, *args, **kwargs):
        logger.info('Importing Acaps Data')
        API_TOKEN = "5800bad4b70fe84dd70a2a760c48cd59b1b0f43d"
        country_name = CountryOverview.objects.filter(country__record_type=CountryType.COUNTRY).values_list('country__name', flat=True)
        for name in country_name:
            SEASONAL_EVENTS_API = f"https://api.acaps.org/api/v1/seasonal-events-calendar/seasonal-calendar/?country={name}"
            response = requests.get(
                SEASONAL_EVENTS_API,
                headers={
                    "Authorization": "Token %s" % API_TOKEN
                }
            )
            response_data = response.json()
            if 'results' in response_data and len(response_data['results']):
                df = pd.DataFrame.from_records(response_data["results"])
                for df_data in df.values.tolist():
                    df_country = df_data[2]
                    if name.lower() == df_country[0].lower():
                        dict_data = {
                            'overview': CountryOverview.objects.filter(country__name=name).first(),
                            'month': df_data[6],
                            'event': df_data[7],
                            'event_type': df_data[8],
                            'label': df_data[9],
                            'source': df_data[11],
                            'source_date': df_data[12]
                        }
                        AcapsSeasonalCalender.objects.create(**dict_data)