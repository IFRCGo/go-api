import datetime as dt
import json

import pandas as pd
import requests
import xmltodict
from bs4 import BeautifulSoup
from dateutil.parser import parse
from django.core.management.base import BaseCommand

from api.logger import logger
from api.models import Country, CountryICRCPresence, CronJob, CronJobStatus


class Command(BaseCommand):
    help = "Add ICRC data"

    def handle(self, *args, **kwargs):
        logger.info("Strating ICRC data ingest")
        response = requests.get(url="https://www.icrc.org/en/where-we-work", headers={"User-Agent": ""})
        if response.status_code != 200:
            text_to_log = "Error querying ICRC feed at " + url
            logger.error(text_to_log)
            logger.error(response.content)
            body = {
                "name": "ingest_icrc",
                "message": text_to_log,
                "status": CronJobStatus.ERRONEOUS,
            }
            CronJob.sync_cron(body)
            raise Exception("Error querying ICRC")

        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Get the countries information from the "Where we work" page
        regions_list = soup.find("div", {"id": "blockRegionalList"}).find_all("ul", {"class": "list"})
        country_list = []
        for region in regions_list:
            for country in region.find_all("li", {"class": "item"}):
                # Get key information
                name = country.text.strip()
                url = country.find("a")["href"] if country.find("a") else None
                presence = True if url else False
                key_operation = True if "keyOperations" in country["class"] else False
                # Get the description from the country page
                description = None
                if url:
                    try:
                        country_page = requests.get(url=url, headers={"User-Agent": ""})
                        country_page.raise_for_status()
                        country_soup = BeautifulSoup(country_page.content, "html.parser")
                        description = country_soup.find("div", {"class": "block-introduction"}).find_all()[2].text.strip()
                    except Exception as err:
                        pass
                # Append all the information to the list
                country_list.append(
                    {
                        "Country": name,
                        "ICRC presence": presence,
                        "URL": url,
                        "Key operation": key_operation,
                        "Description": description,
                    }
                )
        added = 0
        for data in country_list:
            country = Country.objects.filter(name__exact=data["Country"])
            if country.exists():
                dict_data = {
                    "country": country.first(),
                    "icrc_presence": data["ICRC presence"],
                    "url": data["URL"],
                    "key_operation": data["Key operation"],
                    "description": data["Description"],
                }
                added += 1
                CountryICRCPresence.objects.create(**dict_data)

        text_to_log = "%s ICRC added" % added
        logger.info(text_to_log)
        body = {"name": "ingest_icrc", "message": text_to_log, "num_result": added, "status": CronJobStatus.SUCCESSFUL}
        CronJob.sync_cron(body)
