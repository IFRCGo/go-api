import requests
import datetime as dt
import xmltodict
from dateutil.parser import parse
from django.core.management.base import BaseCommand
from api.models import Country, Region, Event, CronJob, CronJobStatus
from api.event_sources import SOURCES
from api.logger import logger


class Command(BaseCommand):
    help = 'Add new event (=emergency) entries from WHO API'

    def handle(self, *args, **options):

        guids = [e.auto_generated_source for e in Event.objects.filter(auto_generated_source__startswith='www.who.int')]

        logger.info('Querying WHO RSS feed for new emergency data')
        # get latest
        nspace = '{https://www.who.int}'
        ur2 = []
        ur2.append('https://www.who.int/feeds/entity/csr/don/en/rss.xml')
        ur2.append('https://www.who.int/feeds/entity/hac/en/rss.xml')

        for index, url in enumerate(ur2):
            response = requests.get(url)
            if response.status_code != 200:
                text_to_log = 'Error querying WHO xml feed at ' + url
                logger.error(text_to_log)
                logger.error(response.content)
                body = { "name": "ingest_who", "message": text_to_log, "status": CronJobStatus.ERRONEOUS } # not every case is catched here, e.g. if the base URL is wrong...
                CronJob.sync_cron(body)
                raise Exception('Error querying WHO')

            # get as XML, but then do not use the obsolate xml2dict = XML2Dict(), but xmltodict
            results = xmltodict.parse(response.content)
            added = 0
            # lastBuildDate = results['rss']['channel']['lastBuildDate']
            # managingEditor = results['rss']['channel']['managingEditor']
            for row in results['rss']['channel']['item']:
                data = {
                    'title': row.pop('title'),
                    'link': row.pop('link'),
                    'description': row.pop('description'),
                    'guid': row['guid']['#text'],
                    'isPermaLink': row['guid']['@isPermaLink'],
                    'category': row.pop('category'),
                    'pubDate': row.pop('pubDate'),
                }
                if data['guid'] in guids:
                    continue
                if data['guid'] in ['WeDontWantThis', 'NeitherThis']:
                    continue

                title = data['title'] # for csr link
                short = title.replace(' (ex-China)','')
                pos = short.find(' – ')
                region = None
                country = None
                if pos == -1:
                    pos = short.find(' - ')
                if pos > 0:
                    country = short[pos+3:] # cutting the part after " – " or " - "
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
                elif country[:4] == 'the ':
                    country = country[4:]
                elif index == 1: # for 'hac' category. See link for 'hac' above
                    hac_category = data['category']

                    # Searching for the given country
                    end = hac_category.find('[country]')
                    if end > 0:
                        start = hac_category[ :end-1].rfind(',', 0) # backwards search the comma
                        country = hac_category[ start+2 : end-1 ] # Getting the comma followed part from the category as Country
                    else:
                        country = 'CountryNotFoundInCategory' # Will not be found via filtering
                    # Searching for the given region
                    end = hac_category.find('[region]')
                    if end > 0:
                        start = hac_category[ :end-1].rfind(',', 0) # backwards search the comma
                        region_name = hac_category[ start+2 : end-1 ] # Getting the comma followed part from the category as Country
                        if 'Afr' in region_name:  # Keep synchronised with https://github.com/IFRCGo/go-api/blob/master/api/models.py#L38-L42
                            region = 0
                        elif 'Ame' in region_name:
                            region = 1
                        elif 'As' in region_name:
                            region = 2
                        elif 'Eu' in region_name:
                            region = 3
                        elif 'MENA' in region_name:
                            region = 4
                        else: # search for region that is joined to country (later)...
                            region = None

                # make sure we don't exceed the 100 character limit
                if len(title) > 99:
                    title = '%s...' % title[:99]
                date = parse(data['pubDate'])
                if data['category'] == 'news':
                    alert_level = 1
                else:
                    alert_level = 2
                if "Ebola" in title or "virus" in title or "fever" in title:
                    alert_level=2
                elif index == 1:
                    alert_level=0

                if data['category'] == 'news':
                    summary = data['description']
                else:
                    summary = data['description'] + ' (' + data['category']+ ')'

                fields = {
                    'name': title,
                    'summary': summary,
                    'disaster_start_date': date,
                    'auto_generated': True,
                    'auto_generated_source': data['guid'],
                    'ifrc_severity_level': alert_level,
                }
                # TODO: fields['name'] sometimes exceeds 100 maxlength, so will need some altering if this will be used
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

                # add region
                # print(country)
                if (region is None) and (country_found.count() > 0) and (country != 'CountryNotFoundInCategory'):
                    region = country_found[0].region_id
                if region is not None:
                    event.regions.add(region)

            text_to_log = "{} WHO messages added, URL-{}".format(added, index + 1)
            logger.info(text_to_log)

            # Database CronJob logging
            body = { "name": "ingest_who", "message": text_to_log, "num_result": added, "storing_days": 6, "status": CronJobStatus.SUCCESSFUL }

            #... via API - not using frosm here, but from front-end it can be useful:
            #resp = requests.post(api_url + '/api/v2/add_cronjob_log/', body, headers={'CONTENT_TYPE': 'application/json'})

            # ... via a direct write-in:
            CronJob.sync_cron(body)

# Testing / db refreshment – hints
# delete from api_event_countries where event_id in (select id from api_event where auto_generated_source like 'www.who.int%');
# delete from api_event_regions where event_id in (select id from api_event where auto_generated_source like 'www.who.int%');
# delete from api_event where auto_generated_source like 'www.who.int%';
# --
# select * from api_event_countries a join api_country b on (a.country_id=b.id) where event_id in (select id from api_event where auto_generated_source like 'www.who.int%');
# select name from api_event a left join api_event_countries b on (a.id=b.event_id) where b.event_id is null and auto_generated_source like 'www.who.int%';  -- what country is not found
