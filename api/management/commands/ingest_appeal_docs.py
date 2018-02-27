import logging
import requests
from datetime import datetime, timezone
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from api.models import Appeal, AppealDocument

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Ingest existing appeal documents'

    def parse_date(self, date_string):
        # 21Dec2017
        timeformat = '%d%b%Y'
        return datetime.strptime(date_string.strip(), timeformat).replace(tzinfo=timezone.utc)

    def handle(self, *args, **options):
        print(datetime.utcnow())

        # get latest
        url = 'https://proxy.hxlstandard.org/data.json?url=https%3A%2F%2Fdocs.google.com%2Fspreadsheets%2Fd%2F1gJ4N_PYBqtwVuJ10d8zXWxQle_i84vDx5dHNBomYWdU%2Fedit%3Fusp%3Dsharing'

        response = requests.get(url)
        if response.status_code != 200:
            raise Exception('Error querying Appeal Document HXL API')
        records = response.json()

        # some logging variables
        not_found = []
        existing = []
        created = []

        # group records by appeal code
        acodes = list(set([a[2] for a in records[2:]]))
        for code in acodes:
            try:
                appeal = Appeal.objects.get(code=code)
            except ObjectDoesNotExist:
                not_found.append(code)
                continue

            existing_docs = list(appeal.appealdocument_set.all())
            docs = [a for a in records if a[2] == code]
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
        print('%s created' % len(created))
        print('%s existing' % len(existing))
        print('%s without appeals in system' % len(not_found))
