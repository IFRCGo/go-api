import requests
from requests.auth import HTTPBasicAuth
import xmltodict
import json

from django.core.management.base import BaseCommand
from api.logger import logger
from api.models import (
    Country,
    CronJob,
    CronJobStatus
)


class Command(BaseCommand):
    help = "Add ns contact details"

    def handle(self, *args, **kwargs):
        logger.info('Starting NS Contacts')
        url = "https://go-api.ifrc.org/"
        headers = {'accept': 'application/xml;q=0.9, */*;q=0.8'}
        response = requests.get(
            "https://go-api.ifrc.org/api/NationalSocieties",
            auth=HTTPBasicAuth("gotestuser", "123456"),
            headers=headers
        )
        if response.status_code != 200:
            text_to_log = "Error querying NationalSocieties xml feed at " + url
            logger.error(text_to_log)
            logger.error(response.content)
            body = {
                "name": "ingest_ns_contact",
                "message": text_to_log,
                "status": CronJobStatus.ERRONEOUS,
            }
            CronJob.sync_cron(body)
            raise Exception("Error querying NationalSocieties")

        added = 0
        dict_data = xmltodict.parse(response.content)
        for data in dict_data['ArrayOfNationalSocietiesMain']['NationalSocietiesMain']:
            address_1 = data['ADD_address1'] if type(data['ADD_address1']) == str else None
            address_2 = data['ADD_address2'] if type(data['ADD_address2']) == str else None
            city_code = data['ADD_city_code'] if type(data['ADD_city_code']) == str else None
            phone = data['ADD_phone'] if type(data['ADD_phone']) == str else None
            website = data['ADD_webSite'] if type(data['ADD_webSite']) == str else None
            email =data['ADD_email'] if type(data['ADD_address2']) == str else None
            iso = data['ADD_country_code']
            # # get the country and try to update the data for those country
            country = Country.objects.filter(iso=iso.upper()).first()
            if country:
                added += 1
                country.address_1 = address_1
                country.address_2 = address_2
                country.city_code = city_code
                country.phone = phone
                country.website = website
                country.email = email
                country.save(
                    update_fields=[
                        'address_1',
                        'address_2',
                        'city_code',
                        'phone',
                        'website',
                        'email'
                    ]
                )
        text_to_log = "%s Ns contact added" % added
        logger.info(text_to_log)
        body = {"name": "ingest_ns_contact", "message": text_to_log, "num_result": added, "status": CronJobStatus.SUCCESSFUL}
        CronJob.sync_cron(body)
