import time

import pandas as pd
import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import models, transaction
from sentry_sdk.crons import monitor

from api.logger import logger
from api.models import CountryType
from databank.models import AcapsSeasonalCalender, CountryOverview
from main.sentry import SentryMonitor


@monitor(monitor_slug=SentryMonitor.INGEST_ACAPS)
class Command(BaseCommand):
    help = "Add Acaps seasonal calender data"

    @transaction.atomic
    def load_country(self, overview):
        # Remove all existing Seasonal Calendar data for this country
        AcapsSeasonalCalender.objects.filter(overview=overview).all().delete()

        name = overview.country_name
        if "," in name:
            name = name.split(",")[0]
        response = requests.get(
            "https://api.acaps.org/api/v1/seasonal-events-calendar/seasonal-calendar/",
            params={"country": name},
            headers={"Authorization": "Token %s" % settings.ACAPS_API_TOKEN},
        )
        logger.info(f"Importing for country {name}")
        response_data = response.json()
        if "results" in response_data and len(response_data["results"]):
            df = pd.DataFrame.from_records(response_data["results"])
            for df_data in df.values.tolist():
                df_country = df_data[2]
                if name.lower() == df_country[0].lower():
                    dict_data = {
                        "overview": overview,
                        "month": df_data[6],
                        "event": df_data[7],
                        "event_type": df_data[8],
                        "label": df_data[9],
                        "source": df_data[11],
                        "source_date": df_data[12],
                    }
                    # Use bulk manager
                    AcapsSeasonalCalender.objects.create(**dict_data)
        # NOTE: Acaps throttles our requests
        time.sleep(5)

    def handle(self, *args, **kwargs):
        logger.info("Importing Acaps Data")
        country_overview_qs = CountryOverview.objects.filter(country__record_type=CountryType.COUNTRY).annotate(
            country_name=models.F("country__name"),
        )
        for overview in country_overview_qs:
            self.load_country(overview)
