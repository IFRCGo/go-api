import requests
import xmltodict
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from requests.auth import HTTPBasicAuth
from sentry_sdk.crons import monitor

from api.logger import logger
from api.models import Country, CountryDirectory, CronJob, CronJobStatus
from main.sentry import SentryMonitor


class Command(BaseCommand):
    help = "Add ns contact details"

    @monitor(monitor_slug=SentryMonitor.INGEST_NS_DIRECTORY)
    @transaction.atomic
    def handle(self, *args, **kwargs):
        def postprocessor(path, key, value):
            if key == "@i:nil":
                return None
            return key, value

        logger.info("Starting NS Contacts")
        url = "https://go-api.ifrc.org/"
        headers = {"accept": "application/xml;q=0.9, */*;q=0.8"}
        response = requests.get(
            "https://go-api.ifrc.org/api/NationalSocietiesContacts/",
            auth=HTTPBasicAuth(settings.NS_CONTACT_USERNAME, settings.NS_CONTACT_PASSWORD),
            headers=headers,
        )
        if response.status_code != 200:
            text_to_log = "Error querying NationalSocietiesContacts xml feed at " + url
            logger.error(text_to_log)
            logger.error(response.content)
            body = {
                "name": "ingest_ns_directory",
                "message": text_to_log,
                "status": CronJobStatus.ERRONEOUS,
            }
            CronJob.sync_cron(body)
            raise Exception("Error querying NationalSocietiesContacts")

        added = 0
        created_country_directory_ids = []
        dict_data = xmltodict.parse(response.content, postprocessor=postprocessor)
        for data in dict_data["ArrayOfNationalSocietiesContacts"]["NationalSocietiesContacts"]:
            country_name = data["CON_country"] if isinstance(data["CON_country"], str) else None
            if country_name is not None:
                country = Country.objects.filter(name__icontains=country_name).first()
                if country:
                    added += 1
                    data = {
                        "first_name": (
                            data["CON_firstName"]
                            if isinstance(data["CON_firstName"], str) and data["CON_firstName"] is not None
                            else None
                        ),
                        "last_name": (
                            data["CON_lastName"]
                            if isinstance(data["CON_lastName"], str) and data["CON_lastName"] is not None
                            else None
                        ),
                        "position": data["CON_title"],
                        "country": country,
                    }
                    country_directory, _ = CountryDirectory.objects.get_or_create(
                        country=country,
                        first_name__iexact=data["first_name"],
                        last_name__iexact=data["last_name"],
                        position__iexact=data["position"],
                        defaults={
                            "first_name": data["first_name"],
                            "last_name": data["last_name"],
                            "position": data["position"],
                        },
                    )
                    created_country_directory_ids.append(country_directory.pk)
        # NOTE: Deleting the country directory which are not available in the source
        CountryDirectory.objects.exclude(id__in=created_country_directory_ids).delete()
        text_to_log = "%s Ns Directory added" % added
        logger.info(text_to_log)
        body = {"name": "ingest_ns_directory", "message": text_to_log, "num_result": added, "status": CronJobStatus.SUCCESSFUL}
        CronJob.sync_cron(body)
