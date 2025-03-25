import numpy as np
import pandas as pd
import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from sentry_sdk.crons import monitor

from api.logger import logger
from api.models import Country, CronJob, CronJobStatus, NSDInitiatives
from main.sentry import SentryMonitor


class Command(BaseCommand):
    help = "Add ns initiatives"

    @monitor(monitor_slug=SentryMonitor.INGEST_NS_INITIATIVES)
    @transaction.atomic
    def handle(self, *args, **kwargs):
        logger.info("Starting NS Inititatives")
        production = settings.GO_ENVIRONMENT == "production"
        # Requires string1|string2|string3 for the three subsystems (NSIA, ESF, CBF):
        api_keys = settings.NS_INITIATIVES_API_KEY.split("|")
        if len(api_keys) != 3:
            logger.info("No proper api-keys are provided. Quitting.")
            return

        if production:
            urls = [
                # languageCode can be en, es, fr, ar. If omitted, defaults to en.
                f"https://data.ifrc.org/NSIA_API/api/approvedApplications?languageCode=en&apiKey={api_keys[0]}",
                f"https://data.ifrc.org/ESF_API/api/approvedApplications?languageCode=en&apiKey={api_keys[1]}",
                f"https://data.ifrc.org/CBF_API/api/approvedApplications?languageCode=en&apiKey={api_keys[2]}",
            ]
        else:
            urls = [
                f"https://data-staging.ifrc.org/NSIA_API/api/approvedApplications?languageCode=en&apiKey={api_keys[0]}",
                f"https://data-staging.ifrc.org/ESF_API/api/approvedApplications?languageCode=en&apiKey={api_keys[1]}",
                f"https://data-staging.ifrc.org/CBF_API/api/approvedApplications?languageCode=en&apiKey={api_keys[2]}",
            ]

        responses = []
        for url in urls:
            response = requests.get(url)
            if response.status_code == 200:
                responses.append(response.json())

        added = 0

        flatList = [element for innerList in responses for element in innerList]
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
                "FundingType",
                "FundingPeriodInYears",
            ],
        )
        funding_data = funding_data.replace({np.nan: None})
        created_ns_initiatives_pk = []
        for data in funding_data.values.tolist():
            # TODO: Filter not by society name
            country = Country.objects.filter(society_name__iexact=data[0]).first()
            if country:
                nsd_initiatives, created = NSDInitiatives.objects.get_or_create(
                    country=country,
                    year=data[1],
                    fund_type=f"{data[2]} – {data[7]}" if data[7] else data[2],
                    defaults={
                        "title": data[3],
                        "categories": data[4],
                        "allocation": data[5],
                        "funding_period": data[6] if data[6] else data[8] * 12,
                    },
                )
                if not created:
                    nsd_initiatives.title = data[3]
                    nsd_initiatives.categories = data[4]
                    nsd_initiatives.allocation = data[5]
                    nsd_initiatives.funding_period = data[6]
                    nsd_initiatives.save(update_fields=["title", "categories", "allocation", "funding_period"])
                created_ns_initiatives_pk.append(nsd_initiatives.pk)
                added += 1
        # NOTE: Delete the NSDInitiatives that are not in the source
        NSDInitiatives.objects.exclude(id__in=created_ns_initiatives_pk).delete()

        text_to_log = "%s Ns initiatives added" % added
        logger.info(text_to_log)
        body = {"name": "ingest_ns_initiatives", "message": text_to_log, "num_result": added, "status": CronJobStatus.SUCCESSFUL}
        CronJob.sync_cron(body)
