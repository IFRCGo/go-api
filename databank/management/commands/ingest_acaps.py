import requests
import datetime as dt
import xmltodict
import pandas as pd
from dateutil.parser import parse

from django.core.management.base import BaseCommand

from api.models import Country, CountryType, CronJob, CronJobStatus, DisasterType
from api.logger import logger


class Command(BaseCommand):
    help = 'Add Acaps seasonal calender data'

    def handle(self, *args, **kwargs):
        logger.info('Importing Acaps Data')
        API_TOKEN = "5800bad4b70fe84dd70a2a760c48cd59b1b0f43d"
        country_name = Country.objects.filter(record_type=CountryType.COUNTRY).values_list('name', flat=True)
        for name in country_name:
            SEASONAL_EVENTS_API = f"https://api.acaps.org/api/v1/seasonal-events-calendar/seasonal-calendar/?country={name}"
            response = requests.get(
                SEASONAL_EVENTS_API,
                headers={
                    "Authorization": "Token %s" % API_TOKEN
                }
            )
            response_data = response.content
            print(response_data)
            df = pd.DataFrame.from_records(response_data["results"])
            print(df)
            break