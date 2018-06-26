import requests
import datetime as dt
from encoder import XML2Dict
from dateutil.parser import parse
from django.core.management.base import BaseCommand
from api.models import Country, Event, GDACSEvent
from api.event_sources import SOURCES
from api.logger import logger


class Command(BaseCommand):
    help = 'Add new entries from Access database file'

    def handle(self, *args, **options):
        logger.info('Starting GDACs ingest')
        # get latest
        nspace = '{http://www.gdacs.org}'
        url = 'http://www.gdacs.org/xml/rss_7d.xml'

        response = requests.get(url)
        if response.status_code != 200:
            logger.error('Error querying GDACS xml feed at http://www.gdacs.org/xml/rss_7d.xml')
            logger.error(response.content)
            raise Exception('Error querying GDACS')

        # get as XML
        xml2dict = XML2Dict()
        results = xml2dict.parse(response.content)
        levels = {'Orange': 1, 'Red': 2}
        added = 0
        for alert in results['rss']['channel']['item']:
            alert_level = alert['%salertlevel' % nspace].decode('utf-8')
            if alert_level in levels.keys():
                latlon = alert['{http://www.georss.org/georss}point'].decode('utf-8').split()
                eid = alert.pop(nspace + 'eventid')
                alert_score = alert[nspace + 'alertscore'] if (nspace + 'alertscore') in alert else None
                data = {
                    'title': alert.pop('title'),
                    'description': alert.pop('description'),
                    'image': alert.pop('enclosure'),
                    'report': alert.pop('link'),
                    'publication_date': parse(alert.pop('pubDate')),
                    'year': alert.pop(nspace + 'year'),
                    'lat': latlon[0],
                    'lon': latlon[1],
                    'event_type': alert.pop(nspace + 'eventtype'),
                    'alert_level': levels[alert_level],
                    'alert_score': alert_score,
                    'severity': alert.pop(nspace + 'severity'),
                    'severity_unit': alert['@' + nspace + 'severity']['unit'],
                    'severity_value': alert['@' + nspace + 'severity']['value'],
                    'population_unit': alert['@' + nspace + 'population']['unit'],
                    'population_value': alert['@' + nspace + 'population']['value'],
                    'vulnerability': alert['@' + nspace + 'vulnerability']['value'],
                    'country_text': alert.pop(nspace + 'country'),
                }

                # do some length checking
                for key in ['event_type', 'alert_score', 'severity_unit', 'severity_value', 'population_unit', 'population_value']:
                    if len(data[key]) > 16:
                        data[key] = data[key][:16]
                data = {k: v.decode('utf-8') if isinstance(v, bytes) else v for k, v in data.items()}
                gdacsevent, created = GDACSEvent.objects.get_or_create(eventid=eid, defaults=data)
                if created:
                    added += 1
                    for c in data['country_text'].split(','):
                        country = Country.objects.filter(name=c.strip())
                        if country.count() == 1:
                            gdacsevent.countries.add(country[0])

                    title_elements = ['GDACS %s:' % alert_level]
                    for field in ['country_text', 'event_type', 'severity']:
                        if data[field] is not None:
                            title_elements.append(str(data[field]))
                    title = (' ').join(title_elements)

                    # make sure we don't exceed the 100 character limit
                    if len(title) > 97:
                        title = '%s...' % title[:97]

                    fields = {
                        'name': title,
                        'summary': data['description'],
                        'disaster_start_date': data['publication_date'],
                        'auto_generated': True,
                        'auto_generated_source': SOURCES['gdacs'],
                        'alert_level': data['alert_level'],
                    }
                    event = Event.objects.create(**fields)
                    # add countries
                    [event.countries.add(c) for c in gdacsevent.countries.all()]

        logger.info('%s GDACs events added' % added)
