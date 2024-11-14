import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from sentry_sdk.crons import monitor

from api.logger import logger
from api.models import Country, CountryICRCPresence, CronJob, CronJobStatus
from main.sentry import SentryMonitor


class Command(BaseCommand):
    help = "Add ICRC data"

    @monitor(monitor_slug=SentryMonitor.INGEST_ICRC)
    def handle(self, *args, **kwargs):
        logger.info("Starting ICRC data ingest")
        HEADERS = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",  # noqa
        }
        icrc_url = "https://www.icrc.org"
        icrc_where_we_work_url = "https://www.icrc.org/en/where-we-work"
        response = requests.get(url=icrc_where_we_work_url, headers=HEADERS)

        if response.status_code != 200:
            text_to_log = "Error querying ICRC feed at https://www.icrc.org/en/where-we-work"
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

        # Get countries information from "Where we work" page
        regions_list = soup.find("div", {"class": "js-select-country-list"}).find("ul").find_all("ul")

        # Holds the list of countries that are part of the key operations
        key_operations_country_list = soup.find("div", {"class": "key-operations-content"}).find_all("div", class_="title")

        # NOTE: Mapping this Country, as it doesnot match with the name in the database
        country_name_mapping = {"Syria": "Syrian Arab Republic", "Israel and the occupied territories": "Israel"}

        country_operations_list = [
            country.text.strip() for key_operation in key_operations_country_list for country in key_operation.find_all("a")
        ]

        countries = []
        for region in regions_list:
            for country in region.find_all("li"):
                name = country.text.strip()
                href = country.find("a")["href"] if country.find("a") else None
                country_url = icrc_url + href if href else None
                presence = bool(country_url)
                description = None
                # Check if country is part of the key operations
                key_operation = name in country_operations_list

                if country_url:
                    try:
                        country_page = requests.get(url=country_url, headers=HEADERS)
                        country_page.raise_for_status()
                        country_soup = BeautifulSoup(country_page.content, "html.parser")
                        description_tag = country_soup.find("div", class_="description").find("div", class_="ck-text")
                        description = description_tag.text.strip() if description_tag else None
                    except Exception:
                        pass

                # Append to list
                countries.append(
                    {
                        "Country": name,
                        "ICRC presence": presence,
                        "URL": country_url,
                        "Key operation": key_operation,
                        "Description": description,
                    }
                )

        added = 0
        created_ns_presence_pk = []
        for data in countries:
            # NOTE: mapping the country name
            data["Country"] = country_name_mapping.get(data["Country"], data["Country"])

            country = Country.objects.filter(name__exact=data["Country"]).first()
            if country:
                country_icrc_presence, _ = CountryICRCPresence.objects.get_or_create(country=country)
                country_icrc_presence.icrc_presence = data["ICRC presence"]
                country_icrc_presence.url = data["URL"]
                country_icrc_presence.key_operation = data["Key operation"]
                country_icrc_presence.description = data["Description"]
                country_icrc_presence.save()
                created_ns_presence_pk.append(country_icrc_presence.pk)
                added += 1
        # NOTE: Delete the CountryICRCPresence that are not in the source
        CountryICRCPresence.objects.exclude(id__in=created_ns_presence_pk).delete()

        text_to_log = f"{added} ICRC added"
        logger.info(text_to_log)
        body = {"name": "ingest_icrc", "message": text_to_log, "num_result": added, "status": CronJobStatus.SUCCESSFUL}
        CronJob.sync_cron(body)
