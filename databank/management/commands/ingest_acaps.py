import time

import pandas as pd
import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from sentry_sdk.crons import monitor

from api.logger import logger
from api.models import CountryType
from databank.models import AcapsSeasonalCalender, CountryOverview
from main.sentry import SentryMonitor


@monitor(monitor_slug=SentryMonitor.INGEST_ACAPS)
class Command(BaseCommand):
    help = "Add Acaps seasonal calender data"

    def handle(self, *args, **kwargs):
        logger.info("Importing Acaps Data")
        country_name = CountryOverview.objects.filter(country__record_type=CountryType.COUNTRY).values_list(
            "country__name", flat=True
        )
        for name in country_name:
            if "," in name:
                name = name.split(",")[0]
            SEASONAL_EVENTS_API = f"https://api.acaps.org/api/v1/seasonal-events-calendar/seasonal-calendar/?country={name}"
            response = requests.get(SEASONAL_EVENTS_API, headers={"Authorization": "Token %s" % settings.ACAPS_API_TOKEN})
            logger.info(f"Importing for country {name}")
            response_data = response.json()
            if "results" in response_data and len(response_data["results"]):
                df = pd.DataFrame.from_records(response_data["results"])
                for df_data in df.values.tolist():
                    df_country = df_data[2]
                    if name.lower() == df_country[0].lower():
                        dict_data = {
                            "overview": CountryOverview.objects.filter(country__name__icontains=name).first(),
                            "month": df_data[6],
                            "event": df_data[7],
                            "event_type": df_data[8],
                            "label": df_data[9],
                            "source": df_data[11],
                            "source_date": df_data[12],
                        }
                        AcapsSeasonalCalender.objects.create(**dict_data)
            time.sleep(5)
