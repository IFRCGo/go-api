import os
import sys
import logging
import requests
from datetime import datetime, timezone, timedelta
from django.core.management.base import BaseCommand
from api.models import AppealType, Appeal, Region, Country, DisasterType, Event
from api.fixtures.dtype_map import DISASTER_TYPE_MAPPING

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
        records = response.json()

        # read from static file for development
        # with open('appeals.json') as f:
        #     records = json.loads(f.read())

        eids = [e.eid for e in Event.objects.all()]
        aids = [a.aid for a in Appeal.objects.all()]

        print('%s current events' % Event.objects.all().count())
        print('%s current appeals' % Appeal.objects.all().count())

        timeformat = '%Y-%m-%dT%H:%M:%S'
        results = []
        since_last_checked = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(minutes=60)
        for r in records:
            if r['APP_Id'] not in eids:
                results.append(r)
            last_modified = datetime.strptime(r['APP_modifyTime'][:18], timeformat).replace(tzinfo=timezone.utc)
            if last_modified > since_last_checked:
                results.append(r)
        print('Ingesting %s events' % len(results))

        for i, r in enumerate(results):
            sys.stdout.write('.') if (i % 100) == 0 else None
            # create an Event for this
            fields = { 'name': r['APP_name'] }

            # get the disaster type mapping
            if r['ADT_name'] in DISASTER_TYPE_MAPPING:
                disaster_name = DISASTER_TYPE_MAPPING[r['ADT_name']]
            else:
                disaster_name = 'Other'
            fields['dtype'] = DisasterType.objects.get(name=disaster_name)

            # get the region mapping
            regions = {'africa': 0, 'americas': 1, 'asia pacific': 2, 'europe': 3, 'middle east and north africa': 4}
            region_name = r['OSR_name'].lower().strip()
            if region_name in regions:
                region = Region.objects.filter(name=regions[region_name])
                fields['region'] = region.first()
            else:
                print('Couldn\'t find a matching region for %s' % r['OSR_name'])

            event, created = Event.objects.get_or_create(eid=r['APP_Id'], defaults=fields)

            # add the country, which can be multiple
            country = Country.objects.filter(name=r['OSC_name'])
            if country.count() == 0:
                country = None
            else:
                country = country.first()
                event.countries.add(country)

            appeals = [a for a in r['Details'] if a['APD_code'] not in aids]
            atypes = {66: AppealType.DREF, 64: AppealType.APPEAL, 1537: AppealType.INTL}
            for appeal in appeals:
                amount_funded = 0 if appeal['ContributionAmount'] is None else appeal['ContributionAmount']
                fields = {
                    'event': event,
                    'atype': atypes[appeal['APD_TYP_Id']],
                    'country': country,
                    'sector': r['OSS_name'],
                    'code': r['APP_code'],
                    'start_date': datetime.strptime(appeal['APD_startDate'], timeformat).replace(tzinfo=timezone.utc),
                    'end_date': datetime.strptime(appeal['APD_endDate'], timeformat).replace(tzinfo=timezone.utc),
                    'status': r['APP_status'],
                    'num_beneficiaries': appeal['APD_noBeneficiaries'],
                    'amount_requested': appeal['APD_amountCHF'],
                    'amount_funded': amount_funded
                }
                item, created = Appeal.objects.get_or_create(aid=appeal['APD_code'], defaults=fields)
                if created:
                    aids.append(appeal['APD_code'])

        print('%s events' % Event.objects.all().count())
        print('%s appeals' % Appeal.objects.all().count())
