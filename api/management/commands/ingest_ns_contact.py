import re
from datetime import datetime

import requests
import xmltodict
from django.conf import settings
from django.core.management.base import BaseCommand
from requests.auth import HTTPBasicAuth

from api.logger import logger
from api.models import Country, CronJob, CronJobStatus


class Command(BaseCommand):
    help = "Add ns contact details"

    def handle(self, *args, **kwargs):
        logger.info("Starting NS Contacts")
        url = "https://go-api.ifrc.org/"
        headers = {"accept": "application/xml;q=0.9, */*;q=0.8"}
        response = requests.get(
            "https://go-api.ifrc.org/api/NationalSocieties",
            auth=HTTPBasicAuth(settings.NS_CONTACT_USERNAME, settings.NS_CONTACT_PASSWORD),
            headers=headers,
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
        for data in dict_data["ArrayOfNationalSocietiesMain"]["NationalSocietiesMain"]:
            address_1 = data["ADD_address1"] if type(data["ADD_address1"]) == str else None
            address_2 = data["ADD_address2"] if type(data["ADD_address2"]) == str else None
            city_code = data["ADD_city_code"] if type(data["ADD_city_code"]) == str else None
            phone = data["ADD_phone"] if type(data["ADD_phone"]) == str else None
            website = data["ADD_webSite"] if type(data["ADD_webSite"]) == str else None
            emails = data["ADD_email"] if type(data["ADD_email"]) == str and data["ADD_email"] != None else None
            founded_date = data["ADD_orgCreation"] if type(data["ADD_orgCreation"]) == str else None
            iso = data["ADD_country_code"]
            # # get the country and try to update the data for those country
            country = Country.objects.filter(iso=iso.upper()).first()
            email_splitted = None
            if emails:
                # NOTE: Split the email
                # eg; secretariatgeneral@creuroja.ad;secretariatadmin@@creuroja.ad
                email_splitted = re.split("[,; ]+", emails)
            if country:
                added += 1
                country.address_1 = address_1
                country.address_2 = address_2
                country.city_code = city_code
                country.phone = phone
                country.website = website
                country.emails = email_splitted
                if founded_date:
                    try:
                        country.founded_date = datetime.strptime(founded_date, "%d.%m.%Y").date()
                    except ValueError:
                        date = founded_date.split(" ")[0]
                        try:
                            country.founded_date = datetime.strptime(date, "%d.%m.%Y").date()
                        except ValueError:
                            try:
                                date = founded_date.split(" ")[-1]
                                country.founded_date = datetime.strptime(date, "%d.%m.%Y").date()
                            except ValueError:
                                pass
                country.save(update_fields=["address_1", "address_2", "city_code", "phone", "website", "emails", "founded_date"])
        text_to_log = "%s Ns contact added" % added
        logger.info(text_to_log)
        body = {"name": "ingest_ns_contact", "message": text_to_log, "num_result": added, "status": CronJobStatus.SUCCESSFUL}
        CronJob.sync_cron(body)
