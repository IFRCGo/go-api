import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from sentry_sdk.crons import monitor

from api.logger import logger
from api.models import Country, CronJob, CronJobStatus
from main.sentry import SentryMonitor


class Command(BaseCommand):
    help = "Add ICRC data"

    @monitor(monitor_slug=SentryMonitor.INGEST_DISASTER_LAW)
    def handle(self, *args, **kwargs):
        logger.info("Starting Disaster Law data")
        home_url = "https://disasterlaw.ifrc.org/"
        region_names = ["africa", "americas", "asia-and-pacific", "middle-east-north-africa", "europe-central-asia"]
        country_list = []
        for region in region_names:
            response = requests.get(f"{home_url}{region}")
            soup = BeautifulSoup(response.content, "html.parser")
            try:
                country_options = soup.find("select", {"data-drupal-selector": "edit-country"}).find_all("option")
            except Exception:
                continue

            # Loop through countries and get information
            duplicated_countries = (("Republic of the Congo", "921"),)
            for option in country_options[1:]:
                country_name = option.text
                country_id = option["value"]
                if (country_name.strip(), str(country_id)) in duplicated_countries:
                    continue
                country_url = f"https://disasterlaw.ifrc.org/node/{country_id}"
                logger.info(f"Importing for country {country_name}")
                # Get the description from the country page
                description = None
                try:
                    country_page = requests.get(country_url)
                    country_soup = BeautifulSoup(country_page.content, "html.parser")
                    description = country_soup.find("div", {"class": "field--name-field-paragraphs"}).find_all("p")
                    description = "\n".join([para.text for para in description])
                except Exception:
                    pass
                # Add all information to the country list
                country_list.append({"Country": country_name, "ID": country_id, "URL": country_url, "Description": description})
        added = 0
        for data in country_list:
            country = Country.objects.filter(name__exact=data["Country"]).first()
            if country:
                country.disaster_law_url = data["URL"] if "URL" in data else None
                country.save(update_fields=["disaster_law_url"])
                added += 1

        text_to_log = "%s Disaster Law" % added
        logger.info(text_to_log)
        body = {"name": "ingest_disaster_law", "message": text_to_log, "num_result": added, "status": CronJobStatus.SUCCESSFUL}
        CronJob.sync_cron(body)
