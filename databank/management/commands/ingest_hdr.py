import logging

import requests
from django.core.management.base import BaseCommand
from django.db import models, transaction
from requests.adapters import HTTPAdapter
from sentry_sdk.crons import monitor
from urllib3.util.retry import Retry

from databank.models import CountryOverview
from main.sentry import SentryMonitor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Add HDR GII data"

    @monitor(monitor_slug=SentryMonitor.INGEST_HDR)
    @transaction.atomic
    def handle(self, *args, **kwargs):
        overview_qs = CountryOverview.objects.annotate(
            country_iso3=models.F("country__iso3"),
        )
        warning_count = 0
        warning_limit = 3
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        session = requests.Session()
        session.mount("https://", HTTPAdapter(max_retries=retry))
        session.mount("http://", HTTPAdapter(max_retries=retry))
        for overview in overview_qs.all():
            if not overview.country_iso3:
                continue
            if warning_count >= warning_limit:
                logger.error(
                    "HDR API warning limit reached (%s); stopping job.",
                    warning_limit,
                )
                break
            try:
                hdr_entities = session.get(
                    "https://api.hdrdata.org/CountryIndicators/filter",
                    params={
                        "country": overview.country_iso3,
                        "year": 2021,
                        "indicator": "gii",
                    },
                    timeout=30,
                )
                hdr_entities.raise_for_status()
                hdr_entities = hdr_entities.json()
            except (requests.RequestException, ValueError) as exc:
                logger.warning("HDR API request error for %s: %s", overview.country_iso3, exc)
                warning_count += 1
                continue

            if len(hdr_entities) == 0:
                continue

            hdr_gii = hdr_entities[0]["value"]
            overview.hdr_gii = hdr_gii
            overview.save(update_fields=["hdr_gii"])
