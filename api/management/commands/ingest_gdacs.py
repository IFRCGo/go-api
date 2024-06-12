import requests
import xmltodict
from dateutil.parser import parse
from django.core.management.base import BaseCommand

from api.event_sources import SOURCES
from api.logger import logger
from api.models import Country, CronJob, CronJobStatus, DisasterType, Event, GDACSEvent


class Command(BaseCommand):
    help = "Add new entries from Access database file"

    def get_disaster_type(self, event_type):
        event_type_map = {
            "EQ": DisasterType.objects.get(name="Earthquake"),
            "TC": DisasterType.objects.get(name="Cyclone"),
            "FL": DisasterType.objects.get(name="Flood"),
            "DR": DisasterType.objects.get(name="Drought"),
            "WF": DisasterType.objects.get(name="Fire"),
        }
        return event_type_map.get(event_type)

    def handle(self, *args, **options):
        logger.info("Starting GDACs ingest")
        nspace = "gdacs:"

        url = "http://www.gdacs.org/xml/rss_7d.xml"
        response = requests.get(url)
        if response.status_code != 200:
            text_to_log = "Error querying GDACS xml feed at " + url
            logger.error(text_to_log)
            logger.error(response.content)
            body = {
                "name": "ingest_gdacs",
                "message": text_to_log,
                "status": CronJobStatus.ERRONEOUS,
            }
            CronJob.sync_cron(body)
            raise Exception("Error querying GDACS")

        results = xmltodict.parse(response.content)
        levels = {"Orange": 1, "Red": 2, "Green": 3}
        added = 0

        for alert in results["rss"]["channel"]["item"]:
            alert_level = alert["%salertlevel" % nspace]
            latlon = alert["georss:point"].split()
            eid = alert.pop(nspace + "eventid")
            alert_score = alert[nspace + "alertscore"] if (nspace + "alertscore") in alert else None
            data = {
                "title": alert.pop("title"),
                "description": alert.pop("description"),
                "image": alert["enclosure"]["@url"],
                "report": alert.pop("link"),
                "publication_date": parse(alert.pop("pubDate")),
                "year": alert.pop(nspace + "year"),
                "lat": latlon[0],
                "lon": latlon[1],
                "event_type": alert[nspace + "eventtype"],
                "alert_level": levels[alert_level],
                "alert_score": alert_score,
                "severity": alert[nspace + "severity"].get("#text"),
                "severity_unit": alert[nspace + "severity"]["@unit"],
                "severity_value": alert[nspace + "severity"]["@value"],
                "population_unit": alert[nspace + "population"]["@unit"],
                "population_value": alert[nspace + "population"]["@value"],
                "vulnerability": alert[nspace + "vulnerability"]["@value"],
                "country_text": alert.pop(nspace + "country"),
                "disaster_type": self.get_disaster_type(alert.pop(nspace + "eventtype")),
            }

            for key in [
                "event_type",
                "alert_score",
                "severity_unit",
                "severity_value",
                "population_unit",
                "population_value",
            ]:
                if len(data[key]) > 16:
                    data[key] = data[key][:16]
            data = {k: v if isinstance(v, bytes) else v for k, v in data.items()}
            gdacsevent, created = GDACSEvent.objects.get_or_create(eventid=eid, defaults=data)
            if created:
                added += 1
                if data["country_text"]:
                    for c in data["country_text"].split(","):
                        country = Country.objects.filter(name__icontains=c.strip())
                        if country.count() == 1:
                            gdacsevent.countries.add(country[0])

                    title_elements = ["GDACS %s:" % alert_level]
                    for field in ["country_text", "event_type", "severity"]:
                        if data[field] is not None:
                            title_elements.append(str(data[field]))
                    title = (" ").join(title_elements)

                    if len(title) > 97:
                        title = "%s..." % title[:97]

                    fields = {
                        "name": title,
                        "summary": data["description"],
                        "disaster_start_date": data["publication_date"],
                        "auto_generated": True,
                        "auto_generated_source": SOURCES["gdacs"],
                        "ifrc_severity_level": data["alert_level"],
                    }
                    event = Event.objects.create(**fields)
                    [event.countries.add(c) for c in gdacsevent.countries.all()]

        text_to_log = "%s GDACs events added" % added
        logger.info(text_to_log)
        body = {"name": "ingest_gdacs", "message": text_to_log, "num_result": added, "status": CronJobStatus.SUCCESSFUL}
        CronJob.sync_cron(body)
