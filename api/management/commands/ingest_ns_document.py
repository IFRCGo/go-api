import json

import numpy as np
import pandas as pd
import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from sentry_sdk.crons import monitor

from api.logger import logger
from api.models import Country, CountryKeyDocument, CronJob, CronJobStatus
from main.sentry import SentryMonitor


class Command(BaseCommand):
    help = "Add ns documents"

    @monitor(monitor_slug=SentryMonitor.INGEST_NS_DOCUMENT)
    @transaction.atomic
    def handle(self, *args, **kwargs):
        logger.info("Starting NS Key Documents")

        # Fetch country codes
        country_code_url = "https://go-api.ifrc.org/api/NationalSocietiesContacts/"
        headers = {"Authorization": f"Basic {settings.NS_INITIATIVES_API_TOKEN}"}
        country_code_response = requests.get(url=country_code_url, headers=headers)

        if country_code_response.status_code != 200:
            self.handle_error(country_code_response)

        country_table = self.extract_country_data(country_code_response.json())

        # Fetch documents for each country
        api_key = settings.NS_DOCUMENT_API_KEY
        result = self.fetch_all_country_documents(api_key, country_table)

        # Save documents to the database
        added = self.save_documents_to_database(result)

        # Log success
        text_to_log = f"{added} Ns key document(s) added"
        logger.info(text_to_log)
        self.sync_cron_success(text_to_log, added)

    def handle_error(self, response):
        text_to_log = f"Error querying NationalSocietiesContacts at {response.url}"
        logger.error(text_to_log)
        logger.error(response.content)
        body = {
            "name": "ingest_ns_document",
            "message": text_to_log,
            "status": CronJobStatus.ERRONEOUS,
        }
        CronJob.sync_cron(body)
        raise Exception("Error querying NationalSocietiesContacts")

    def extract_country_data(self, data):
        country_list = []
        for country_data in data:
            country_code = [country_data["Don_Code"].strip(), country_data["CON_country"]]
            country_list.append(country_code)

        country_table = pd.DataFrame(country_list, columns=["Country Code", "Country"]).drop_duplicates(
            subset=["Country Code"], keep="last"
        )
        country_table = country_table.replace(to_replace="None", value=np.nan).dropna()
        return country_table

    def fetch_country_documents(self, api_key, country_ns_code):
        url = f"https://data-api.ifrc.org/api/documents?apiKey={api_key}&ns={country_ns_code}"
        response = requests.get(url)
        data = json.loads(response.text)
        if not data:
            return None
        documents = []
        for item in data["documents"]:
            document_info = {
                "name": item["name"],
                "url": item["url"],
                "thumbnail": item["thumbnail"],
                "year": str(item["year"]) + "-01-01",
                "end_year": str(item["EndYear"]) + "-01-01" if "EndYear" in item else None,
                "year_text": item["YearText"],
                "document_type": item["document_type"],
                "country_code": country_ns_code,
            }
            documents.append(document_info)
        return documents

    def fetch_all_country_documents(self, api_key, country_table):
        result = []
        for country_data in country_table.values.tolist():
            country_ns_code = country_data[0]
            logger.info(f"Fetching Document for country {country_data[1]}")
            country_documents = self.fetch_country_documents(api_key, country_ns_code)
            if country_documents:
                result.extend(country_documents)
        return result

    def save_documents_to_database(self, result):
        added = 0
        created_country_key_document_ids = []
        for document in result:
            country = Country.objects.filter(fdrs=document["country_code"]).first()
            if country is None:
                continue

            country_key_document, created = CountryKeyDocument.objects.get_or_create(
                country=country,
                url=document["url"],
                defaults={
                    "name": document["name"],
                    "thumbnail": document["thumbnail"],
                    "document_type": document["document_type"],
                    "year": document["year"],
                    "end_year": document["end_year"],
                    "year_text": document["year_text"],
                },
            )
            if not created:
                country_key_document.name = document["name"]
                country_key_document.thumbnail = document["thumbnail"]
                country_key_document.document_type = document["document_type"]
                country_key_document.year = document["year"]
                country_key_document.end_year = document["end_year"]
                country_key_document.year_text = document["year_text"]
                country_key_document.save(
                    update_fields=[
                        "name",
                        "thumbnail",
                        "document_type",
                        "year",
                        "end_year",
                        "year_text",
                    ]
                )
            created_country_key_document_ids.append(country_key_document.pk)
            added += 1
        # NOTE: Deleting the CountryKeyDocument that are not in the source
        CountryKeyDocument.objects.exclude(id__in=created_country_key_document_ids).delete()
        return added

    def sync_cron_success(self, text_to_log, added):
        body = {"name": "ingest_ns_document", "message": text_to_log, "num_result": added, "status": CronJobStatus.SUCCESSFUL}
        CronJob.sync_cron(body)
