import os
import sys
import logging
import requests
import json
from datetime import datetime, timezone
from django.core.management.base import BaseCommand
from api.models import Appeal, Country, DisasterType, Event

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Add new entries from Access database file'

    def handle(self, *args, **options):
        # get latest
        url = 'http://go-api.ifrc.org/api/appeals'

        auth = (os.getenv('APPEALS_USER'), os.getenv('APPEALS_PASS'))
        response = requests.get(url, auth=auth)
        if response.status_code != 200:
            raise Exception('Error querying Appeals API')
        results = response.json()

        # read from static file for development
        # with open('appeals.json') as f:
        #     results = json.loads(f.read())

        eids = [e.eid for e in Event.objects.all()]
        aids = [a.aid for a in Appeal.objects.all()]

        print('%s current events' % Event.objects.all().count())
        print('%s current appeals' % Appeal.objects.all().count())

        results = [r for r in results if r['APP_Id'] not in eids]
        print('Ingesting %s events' % len(results))

        timeformat = '%Y-%m-%dT%H:%M:%S'

        for i, r in enumerate(results):
            sys.stdout.write('.') if (i % 100) == 0 else None
            # create an Event for this
            dtype = DisasterType.objects.filter(name=r['ADT_name']).first()
            if dtype is None:
                dtype = DisasterType.objects.filter(name='Other').first()

            fields = {
                'name': r['APP_name'],
                'dtype': dtype,
                'status': r['APP_status'],
                'region': r['OSR_name'],
                'code': r['APP_code'],
            }
            event, created = Event.objects.get_or_create(eid=r['APP_Id'], defaults=fields)
            if created:
                eids.append(r['APP_Id'])

            country = Country.objects.filter(name=r['OSC_name'])
            if country.count() == 0:
                country = None
            else:
                country = country.first()

            appeals = [a for a in r['Details'] if a['APD_code'] not in aids]
            for appeal in appeals:
                amount_funded = 0 if appeal['ContributionAmount'] is None else appeal['ContributionAmount']
                fields = {
                    'event': event,
                    'country': country,
                    'sector': r['OSS_name'],
                    'start_date': datetime.strptime(appeal['APD_startDate'], timeformat).replace(tzinfo=timezone.utc),
                    'end_date': datetime.strptime(appeal['APD_endDate'], timeformat).replace(tzinfo=timezone.utc),
                    'num_beneficiaries': appeal['APD_noBeneficiaries'],
                    'amount_requested': appeal['APD_amountCHF'],
                    'amount_funded': amount_funded
                }
                item, created = Appeal.objects.get_or_create(aid=appeal['APD_code'], defaults=fields)
                if created:
                    aids.append(appeal['APD_code'])

        print('%s events' % Event.objects.all().count())
        print('%s appeals' % Appeal.objects.all().count())
