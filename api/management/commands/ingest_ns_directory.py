import requests
from requests.auth import HTTPBasicAuth
import xmltodict
import json

from django.core.management.base import BaseCommand
from api.logger import logger
from api.models import (
    Country,
    CountryDirectory,
    CronJob,
    CronJobStatus,
)


class Command(BaseCommand):
    help = "Add ns contact details"

    def handle(self, *args, **kwargs):
        logger.info('Starting NS Contacts')
        url = "https://go-api.ifrc.org/"
        headers = {'accept': 'application/xml;q=0.9, */*;q=0.8'}
        response = requests.get(
            "https://go-api.ifrc.org/api/NationalSocietiesContacts/",
            auth=HTTPBasicAuth("gotestuser", "123456"),
            headers=headers
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
        dict_data = xmltodict.parse(response.content)
        for data in dict_data['ArrayOfNationalSocietiesContacts']['NationalSocietiesContacts']:
            country_name = data['CON_country'] if type(data['CON_country']) == str else None
            if country_name is not None:
                country = Country.objects.filter(name__icontains=country_name).first()
                if country:
                    added += 1
                    data = {
                        'first_name': data['CON_firstName'],
                        'last_name': data['CON_lastName'],
                        'position': data['CON_title'],
                        'country': country,
                    }
                    CountryDirectory.objects.create(**data)
        text_to_log = "%s Ns Directory added" % added
        logger.info(text_to_log)
        body = {"name": "ingest_ns_directory", "message": text_to_log, "num_result": added, "status": CronJobStatus.SUCCESSFUL}
        CronJob.sync_cron(body)
