import requests
import datetime as dt
from encoder import XML2Dict
from dateutil.parser import parse
from django.core.management.base import BaseCommand
from api.models import Country, Event, GDACSEvent
from api.event_sources import SOURCES
from api.logger import logger


class Command(BaseCommand):
    help = 'Add new event (=emergency) entries from WHO API'

    def handle(self, *args, **options):

        guids = [e.auto_generated_source for e in Event.objects.filter(auto_generated_source__startswith='www.who.int')]

        logger.info('Querying WHO RSS feed for new emergency data')
        # get latest
        nspace = '{https://www.who.int}'
        url = 'https://www.who.int/feeds/entity/csr/don/en/rss.xml'


        response = requests.get(url)
        if response.status_code != 200:
            logger.error('Error querying WHO xml feed at https://www.who.int/feeds/entity/csr/don/en/rss.xml')
            logger.error(response.content)
            raise Exception('Error querying WHO')

        # get as XML
        xml2dict = XML2Dict()
        results = xml2dict.parse(response.content)
        added = 0
        # import pdb; pdb.set_trace()
        lastBuildDate = results['rss']['channel']['lastBuildDate']
        managingEditor =  results['rss']['channel']['managingEditor']
        for row in results['rss']['channel']['item']:
            data = {
                'title': row.pop('title'),
                'link': row.pop('link'),
                'description': row.pop('description'),
                'guid': row.pop('guid'),
#               '@guid': row.pop('@guid'),  #can not be popped twice
                'isPermaLink': row.pop('@guid').pop('isPermaLink'),
                'category': row.pop('category'),
                'pubDate': row.pop('pubDate'),
            }
            if data['guid'].decode("utf-8") in guids:
                continue
            if data['guid'].decode("utf-8") in ['WeDontWantThis', 'NeitherThis']:
                continue

#            alert_level = alert['%salertlevel' % nspace].decode('utf-8')
#            if alert_level in levels.keys():
#                latlon = alert['{http://www.georss.org/georss}point'].decode('utf-8').split()
#                eid = alert.pop(nspace + 'eventid')
#                alert_score = alert[nspace + 'alertscore'] if (nspace + 'alertscore') in alert else None
#                data = {
#                    'title': alert.pop('title'),
#                    'description': alert.pop('description'),
#                    'image': alert.pop('enclosure'),
#                    'report': alert.pop('link'),
#                    'publication_date': parse(alert.pop('pubDate')),
#                    'year': alert.pop(nspace + 'year'),
#                    'lat': latlon[0],
#                    'lon': latlon[1],
#                    'event_type': alert.pop(nspace + 'eventtype'),
#                    'alert_level': levels[alert_level],
#                    'alert_score': alert_score,
#                    'severity': alert.pop(nspace + 'severity'),
#                    'severity_unit': alert['@' + nspace + 'severity']['unit'],
#                    'severity_value': alert['@' + nspace + 'severity']['value'],
#                    'population_unit': alert['@' + nspace + 'population']['unit'],
#                    'population_value': alert['@' + nspace + 'population']['value'],
#                    'vulnerability': alert['@' + nspace + 'vulnerability']['value'],
#                    'country_text': alert.pop(nspace + 'country'),
#                }
#
#                # do some length checking
#                for key in ['event_type', 'alert_score', 'severity_unit', 'severity_value', 'population_unit', 'population_value']:
#                    if len(data[key]) > 16:
#                        data[key] = data[key][:16]
#                data = {k: v.decode('utf-8') if isinstance(v, bytes) else v for k, v in data.items()}
#                gdacsevent, created = GDACSEvent.objects.get_or_create(eventid=eid, defaults=data)
#                if created:
#                    added += 1
#                    for c in data['country_text'].split(','):
#                        country = Country.objects.filter(name=c.strip())
#                        if country.count() == 1:
#                            gdacsevent.countries.add(country[0])
#
#                    title_elements = ['GDACS %s:' % alert_level]
#                    for field in ['country_text', 'event_type', 'severity']:
#                        if data[field] is not None:
#                            title_elements.append(str(data[field]))
#                    title = (' ').join(title_elements)
#
            title = data['title'].decode("utf-8")
            pos = title.find(' – ')
            if pos == -1:
                pos = title.find(' - ')
            if pos > 0:
                country = title[pos+3:] # cutting the part after " – " or " - "
            else:
                country = 'DashNotFoundInTitle'
            if country == 'Democratic Republic of the Congo': #replacement
                country = 'Congo, Dem. Rep.' 
            elif country == 'Argentine Republic':
                country = 'Argentina'
            elif country == 'Republic of Panama':
                country = 'Panama'
            elif country == 'Islamic Republic of Pakistan':
                country = 'Pakistan'
            # make sure we don't exceed the 100 character limit
            if len(title) > 99:
                title = '%s...' % title[:99]
            date = parse(data['pubDate'].decode("utf-8"))
            if data['category'].decode("utf-8") == 'news':
                alert_level = 0
            else:
                alert_level = 1
                
            fields = {
                'name': title,
                'summary': data['description'].decode("utf-8"),
                'disaster_start_date': date,
                'auto_generated': True,
                'auto_generated_source': data['guid'].decode("utf-8"),
                'alert_level': alert_level,
            }
            event = Event.objects.create(**fields)
            added += 1

            # add country
            country_found = Country.objects.filter(name=country.strip())
            if country_found.count() >= 1:
                event.countries.add(country_found[0])
            else:
                country_word_list = country.split()  # list of country words
                country_found = Country.objects.filter(name=country_word_list[-1].strip()) # Search only the last word, like "Republic of Panama" > "Panama"
                if country_found.count() >= 1:
                    event.countries.add(country_found[0])


        logger.info('%s WHO messages added' % added)

# delete from api_event_countries where event_id in (select id from api_event where auto_generated_source like 'www.who.int%'); delete from api_event where auto_generated_source like 'www.who.int%';
# select * from api_event_countries a join api_country b on (a.country_id=b.id) where event_id in (select id from api_event where auto_generated_source like 'www.who.int%');
# select name from api_event a left join api_event_countries b on (a.id=b.event_id) where b.event_id is null and auto_generated_source like 'www.who.int%';  -- what country is not found


