from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from urllib3 import PoolManager
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from api.models import Appeal, AppealDocument, CronJob, CronJobStatus
from api.logger import logger
from collections import defaultdict

class Command(BaseCommand):
    help = 'Ingest existing appeal documents'

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--fullscan',
            action='store_true',
            help='Run a full scan on all appeals',
        )

    def makelist(self, table):
        result = []
        allrows = table.findAll('tr')
        for row in allrows:
            rowData, url = defaultdict(list), ''
            for a in row.find_all('a', href=True):
                url = a['href']

            rowData['url'] = url
            allCols = row.findAll('td')
            for col in allCols:
                thestrings = [s.strip() for s in col.findAll(text=True)]
                thetext = ''.join(thestrings)
                if len(thetext) > 1 and 'data-label' in col.attrs:
                    key = col.attrs['data-label'].lower().replace(" ", "")
                    # key can be: url (above), name, location, appealcode, disastertype, appealtype, date
                    # Example values: "Severe winter", "Grok", "MD...2", "Cold Wave", "DREF Operation Update", "21 Dec 2017"
                    rowData[key] = thetext
            result.append(rowData)
        return result

    def parse_date(self, date_string):
        # 21 Dec 2017
        timeformat = '%d %b %Y'
        return datetime.strptime(date_string.strip(), timeformat).replace(tzinfo=timezone.utc)

    def handle(self, *args, **options):
        logger.info('Starting appeal document ingest')

        # v smoke test
        baseurl = 'https://www.ifrc.org/appeals/'  # no more ...en/publications-and-reports...
        http = PoolManager()  # stackoverflow.com/questions/36516183/what-should-i-use-to-open-a-url-instead-of-urlopen-in-urllib3
        smoke_response = http.request('GET', baseurl)
        joy_to_the_world = False
        if smoke_response.status == 200:
            joy_to_the_world = True  # We log the success later, when we know the numeric results.
        else:
            body = {
                "name": "ingest_appeal_docs",
                "message": f'Error ingesting appeals_docs on url: {baseurl}, error_code: {smoke_response.code}',
                "status": CronJobStatus.ERRONEOUS
            }
            CronJob.sync_cron(body)
        # ^ smoke test

        if options['fullscan']:
            # If the `--fullscan` option is passed (at the end of command), check ALL appeals. Runs an hour!
            print('Doing a full scan of all Appeals')
            qset = Appeal.objects.all()
        else:
            # By default, only check appeals for the past 3 months where Appeal Documents is 0
            now = datetime.now().replace(tzinfo=timezone.utc)
            six_months_ago = now - relativedelta(months=6)
            # This was the original qset, but it wouldn't get newer docs for the same Appeals
            # qset = Appeal.objects.filter(appealdocument__isnull=True).filter(end_date__gt=six_months_ago)
            qset = Appeal.objects.filter(end_date__gt=six_months_ago)

        # qset = Appeal.objects.filter(code='Something')  # could help debug
        # First get all Appeal Codes
        appeal_codes = [a.code for a in qset]

        # Modify code taken from https://pastebin.com/ieMe9yPc to scrape `publications-and-reports` and find
        # Documents for each appeal code
        output = []
        page_not_found = []
        for code in appeal_codes:
            code = code.replace(' ', '')
            docs_url = f'{baseurl}?appeal_code={code}'  # no more ac={code}&at=0&c=&co=&dt=1&f=&re=&t=&ti=&zo=
            try:
                http = PoolManager()
                response = http.request('GET', docs_url)
            except Exception:  # if we get an error fetching page for an appeal, we ignore it
                page_not_found.append(code)
                continue

            soup = BeautifulSoup(response.data, "lxml")
            div = soup.find('div', class_='row appeals-view__row')
            for t in div.findAll('tbody'):
                output = output + self.makelist(t)

        # Once we have all Documents in output, we add all missing Documents to the associated Appeal
        not_found = []
        existing = []
        created = []

        acodes = list(set([a['appealcode'] for a in output]))
        for code in acodes:
            try:
                appeal = Appeal.objects.get(code=code)
            except ObjectDoesNotExist:
                not_found.append(code)
                continue

            existing_docs = list(appeal.appealdocument_set.all())
            docs = [a for a in output if code == a['appealcode']]
            for doc in docs:
                if doc['url'].startswith('/'):  # can be /docs or /sites also
                    doc['url'] = f'https://www.ifrc.org{doc["url"]}'
                    # href only contains relative path to the document if it's available at the ifrc.org site
                exists = len([a for a in existing_docs if a.document_url == doc['url']]) > 0
                if exists:
                    existing.append(doc['url'])
                else:
                    try:
                        created_at = self.parse_date(doc['date'])
                    except Exception:
                        created_at = None

                    AppealDocument.objects.create(
                        document_url=doc['url'],
                        name=doc['appealtype'],  # not ['name'], because this is the appeal's name
                        created_at=created_at,
                        appeal=appeal,
                    )
                    created.append(doc['url'])
        text_to_log = []
        text_to_log.append('%s appeal documents created' % len(created))
        text_to_log.append('%s existing appeal documents' % len(existing))
        text_to_log.append('%s pages not found for appeal' % len(page_not_found))

        for t in text_to_log:
            logger.info(t)
            # body = { "name": "ingest_appeal_docs", "message": t, "status": CronJobStatus.SUCCESSFUL }
            # CronJob.sync_cron(body)

        if len(not_found):
            t = '%s documents without appeals in system' % len(not_found)
            logger.warning(t)
            body = {
                "name": "ingest_appeal_docs",
                "message": t,
                "num_result": len(not_found),
                "status": CronJobStatus.WARNED
            }
            CronJob.sync_cron(body)

        if (joy_to_the_world):
            body = {
                "name": "ingest_appeal_docs",
                "message": (
                    f'Done ingesting appeals_docs on url {baseurl},'
                    f' {len(created)} appeal document(s) were created,'
                    f' {len(existing)} already exist,'
                    f' {len(page_not_found)} not found'
                ),
                "num_result": len(created),
                "status": CronJobStatus.SUCCESSFUL
            }
            CronJob.sync_cron(body)
