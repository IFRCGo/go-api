import logging

import requests
from django.core.management.base import BaseCommand
from sentry_sdk.crons import monitor

from databank.models import CountryOverview as CO
from main.sentry import SentryMonitor

logger = logging.getLogger(__name__)


@monitor(monitor_slug=SentryMonitor.INGEST_HDR)
class Command(BaseCommand):
    help = "Add HDR GII data"

    def handle(self, *args, **kwargs):
        for overview in CO.objects.all():
            HDR_API = f"https://api.hdrdata.org/CountryIndicators/filter?country={overview.country.iso3}&year=2021&indicator=gii"
            hdr_entities = requests.get(HDR_API)
            if hdr_entities.status_code != 200:
                continue
            hdr_entities.raise_for_status()
            hdr_entities = hdr_entities.json()
            if len(hdr_entities):
                hdr_gii = hdr_entities[0]["value"]
                overview.hdr_gii = hdr_gii
                overview.save(update_fields=["hdr_gii"])
