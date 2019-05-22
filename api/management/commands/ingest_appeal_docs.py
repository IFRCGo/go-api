import requests
from datetime import datetime, timezone
from urllib.request import urlopen
import json
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from api.models import Appeal, AppealDocument
from api.logger import logger


class Command(BaseCommand):
    help = 'Ingest existing appeal documents'

    def makelist(self, table):
        result = []
        allrows = table.findAll('tr')
        for row in allrows:
            url=''
            for a in row.find_all('a', href=True):
                url = a['href']
            result.append([url])
            allcols = row.findAll('td')
            for col in allcols:
                thestrings = [s.strip() for s in col.findAll(text=True)]
                thetext = ''.join(thestrings)
                result[-1].append(thetext)
        return result

    def parse_date(self, date_string):
        # 21Dec2017
        timeformat = '%d%b%Y'
        return datetime.strptime(date_string.strip(), timeformat).replace(tzinfo=timezone.utc)

    def handle(self, *args, **options):
        logger.info('Starting appeal document ingest')

        # First get all Appeal Codes
        appeal_codes = [a.code for a in Appeal.objects.all()

        # Modify code taken from https://pastebin.com/ieMe9yPc to scrape `publications-and-reports` and find
        # Documents for each appeal code
        output = []
        for code in appeal_codes:
            print(code)
            docs_url = 'http://www.ifrc.org/en/publications-and-reports/appeals/?ac='+code+'&at=0&c=&co=&dt=1&f=&re=&t=&ti=&zo='
            response = urlopen(docs_url)
            soup = BeautifulSoup(response.read(), "lxml")
            div = soup.find('div', id='cw_content')
            for t in div.findAll('tbody'):
                print(self.makelist(t))
                output = output + self.makelist(t)

        # Once we have all Documents in output, we add all missing Documents to the associated Appeal
        not_found = []
        existing = []
        created = []

        acodes = list(set([a[2] for a in output]))
        for code in acodes:
            try:
                appeal = Appeal.objects.get(code=code)
            except ObjectDoesNotExist:
                not_found.append(code)
                continue

            existing_docs = list(appeal.appealdocument_set.all())
            docs = [a for a in output if a[2] == code]
            for doc in docs:
                exists = len([a for a in existing_docs if a.document_url == doc[0]]) > 0
                if exists:
                    existing.append(doc[0])
                else:
                    try:
                        created_at = self.parse_date(doc[5])
                    except:
                        created_at = None

                    AppealDocument.objects.create(
                        document_url=doc[0],
                        name=doc[4],
                        created_at=created_at,
                        appeal=appeal,
                    )
                    created.append(doc[0])
        logger.info('%s appeal documents created' % len(created))
        logger.info('%s existing appeal documents' % len(existing))
        logger.warn('%s documents without appeals in system' % len(not_found))
