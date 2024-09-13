import logging

import requests
from django.core.management.base import BaseCommand
from sentry_sdk.crons import monitor

from databank.models import CountryOverview as CO
from main.sentry import SentryMonitor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Add Unicef population data"

    @monitor(monitor_slug=SentryMonitor.INGEST_UNICEF)
    def handle(self, *args, **kwargs):
        for overview in CO.objects.all():
            UNICEF_API = f"https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/data/UNICEF,DM,1.0/{overview.country.iso3}.DM_POP_U18._T._T.?format=sdmx-json"  # noqa: E501
            unicef_entities = requests.get(UNICEF_API)
            if unicef_entities.status_code != 200:
                continue
            unicef_entities.raise_for_status()
            unicef_entities = unicef_entities.json()
            population_under_18 = unicef_entities["data"]["dataSets"][0]["series"]["0:0:0:0:0"]["observations"]["73"][0]
            overview.unicef_population_under_18 = float(population_under_18) * 1000
            overview.save(update_fields=["unicef_population_under_18"])
