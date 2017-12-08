import os
import logging
import requests
import datetime as dt
from xml.etree import ElementTree
from encoder import XML2Dict
from dateutil.parser import parse
from django.core.management.base import BaseCommand
from api.models import AppealType, Appeal, Country, DisasterType, Event, GDACSEvent
from api.fixtures.dtype_map import DISASTER_TYPE_MAPPING
from pdb import set_trace

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Add new entries from Access database file'

    def handle(self, *args, **options):
        # get latest
        now = dt.datetime.now()
        start_date = (now - dt.timedelta(days=3)).date()
        end_date = now.date()
        nspace = '{http://www.gdacs.org}'
        url = 'http://gdacs.org/rss.aspx'

        data = {
            'profile': 'ARCHIVES',
            'fromarchive': 'true',
            'from': str(start_date),
            'to': str(end_date)
        }

        response = requests.get(url, params=data)
        if response.status_code != 200:
            raise Exception('Error querying GDACS')

        # get as XML
        xml2dict = XML2Dict()
        results = xml2dict.parse(response.content)
        levels = ['Orange', 'Red']
        added = 0
        for alert in results['rss']['channel']['item']:
            alert_level = alert['%salertlevel' % nspace].decode('utf-8')
            if alert_level in levels:
                latlon = alert['{http://www.georss.org/georss}point'].decode('utf-8').split()

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
                    'alert_level': alert.pop(nspace + 'alertlevel'),
                    #'alertscore': alert[nspace + 'alertscore'],
                    'severity': alert.pop(nspace + 'severity'),
                    'severity_unit': alert['@' + nspace + 'severity']['unit'],
                    'severity_value': alert['@' + nspace + 'severity']['value'],
                    'population_unit': alert['@' + nspace + 'population']['unit'],
                    'population_value': alert['@' + nspace + 'population']['value'],
                    'vulnerability': alert['@' + nspace + 'vulnerability']['value'],
                    'country': alert.pop(nspace + 'country'),
                }
                data = {k: v.decode('utf-8') if isinstance(v, bytes) else v for k, v in data.items()}
                event, created = GDACSEvent.objects.get_or_create(eventid=alert.pop(nspace + 'eventid'), defaults=data)
                if created:
                    added += 1

        print('%s events added' % added)