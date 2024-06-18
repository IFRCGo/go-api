import logging

import requests
from django.core.management.base import BaseCommand
from django.db import models
from sentry_sdk.crons import monitor

from databank.models import CountryOverview
from main.sentry import SentryMonitor

logger = logging.getLogger(__name__)


@monitor(monitor_slug=SentryMonitor.INGEST_HDR)
class Command(BaseCommand):
    help = "Add HDR GII data"

    def handle(self, *args, **kwargs):
        overview_qs = CountryOverview.objects.annotate(
            country_iso3=models.F("country__iso3"),
        )
        for overview in overview_qs.all():
            hdr_entities = requests.get(
                "https://api.hdrdata.org/CountryIndicators/filter",
                params={
                    "country": overview.country_iso3,
                    "year": 2021,
                    "indicator": "gii",
                },
            )
            if hdr_entities.status_code != 200:
                continue
            hdr_entities.raise_for_status()
            hdr_entities = hdr_entities.json()

            if len(hdr_entities) == 0:
                continue

            hdr_gii = hdr_entities[0]["value"]
            overview.hdr_gii = hdr_gii
            overview.save(update_fields=["hdr_gii"])
