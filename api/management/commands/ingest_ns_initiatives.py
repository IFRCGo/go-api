import numpy as np
import pandas as pd
import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from sentry_sdk.crons import monitor

from api.logger import logger
from api.models import Country, CronJob, CronJobStatus, NSDInitiatives
from main.sentry import SentryMonitor


@monitor(monitor_slug=SentryMonitor.INGEST_NS_INITIATIVES)
class Command(BaseCommand):
    help = "Add ns initiatives"

    def handle(self, *args, **kwargs):
        logger.info("Starting NS Inititatives")
        api_key = settings.NS_INITIATIVES_API_KEY
        esf_url = requests.get(f"https://data-api.ifrc.org/api/esf?apikey={api_key}")
        nsia_url = requests.get(f"https://data-api.ifrc.org/api/nsia?apikey={api_key}")
        cbf_url = requests.get(f"https://data-api.ifrc.org/api/cbf?apikey={api_key}")

        # resposne for individual request
        esf_response = esf_url.json()
        nsia_response = nsia_url.json()
        cbf_response = cbf_url.json()

        added = 0

        all_fund_data = [esf_response, nsia_response, cbf_response]
        flatList = [element for innerList in all_fund_data for element in innerList]
        funding_data = pd.DataFrame(
            flatList,
            columns=[
                "NationalSociety",
                "Year",
                "Fund",
                "InitiativeTitle",
                "Categories",
                "AllocationInCHF",
                "FundingPeriodInMonths",
            ],
        )
        funding_data = funding_data.replace({np.nan: None})
        for data in funding_data.values.tolist():
            # TODO: Filter not by society name
            country = Country.objects.filter(society_name__iexact=data[0]).first()
            if country:
                dict_data = {
                    "country": country,
                    "title": data[3],
                    "fund_type": data[2],
                    "allocation": data[5],
                    "year": data[1],
                    "funding_period": data[6],
                    "categories": data[4],
                }
                added += 1
                NSDInitiatives.objects.create(**dict_data)
        text_to_log = "%s Ns initiatives added" % added
        logger.info(text_to_log)
        body = {"name": "ingest_ns_initiatives", "message": text_to_log, "num_result": added, "status": CronJobStatus.SUCCESSFUL}
        CronJob.sync_cron(body)
