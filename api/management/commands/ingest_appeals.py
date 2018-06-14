import os
import sys
import logging
import requests
import json
from datetime import datetime, timezone, timedelta
from django.core.management.base import BaseCommand
from api.models import AppealType, AppealStatus, Appeal, Region, Country, DisasterType, Event
from api.fixtures.dtype_map import DISASTER_TYPE_MAPPING

dtype_keys = [a.lower() for a in DISASTER_TYPE_MAPPING.keys()]
dtype_vals = [a.lower() for a in DISASTER_TYPE_MAPPING.values()]

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Add new entries from Access database file'

    def parse_date(self, date_string):
        timeformat = '%Y-%m-%dT%H:%M:%S'
        return datetime.strptime(date_string[:18], timeformat).replace(tzinfo=timezone.utc)

    def handle(self, *args, **options):
        use_local_file = True if os.getenv('DJANGO_DB_NAME') == 'test' and os.path.exists('appeals.json') else False

        if use_local_file:
            # read from static file for development
            print('Using local appeals.json file')
            with open('appeals.json') as f:
                new_or_modified = json.loads(f.read())
        else:
            # get latest, determine which appeals need to be ingested based on last modified time
            print('Querying appeals API for new appeals data')
            url = 'http://go-api.ifrc.org/api/appeals'
            auth = (os.getenv('APPEALS_USER'), os.getenv('APPEALS_PASS'))
            response = requests.get(url, auth=auth)
            if response.status_code != 200:
                raise Exception('Error querying Appeals API')
            records = response.json()

            # write the current record file to local disk
            with open('appeals.json', 'w') as outfile:
                json.dump(records, outfile)

            since_last_checked = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(minutes=60)
            codes = [a.code for a in Appeal.objects.all()]
            new_or_modified = []
            for r in records:
                if not r['APP_code'] in codes:
                    new_or_modified.append(r)
                last_modified = self.parse_date(r['APP_modifyTime'])
                if last_modified > since_last_checked:
                    new_or_modified.append(r)

        print('%s current appeals' % Appeal.objects.all().count())
        print('Ingesting %s appeals' % len(new_or_modified))

        num_created = 0
        num_updated = 0
        for i, r in enumerate(new_or_modified):
            # get the disaster type mapping
            dname = '' if not r['ADT_name'] else r['ADT_name'].lower()
            # sometimes for some reason the string starts with a period
            if dname and dname[0] == '.':
                dname = dname[1:]

            if dname in dtype_keys:
                idx = dtype_keys.index(dname)
                disaster_name = DISASTER_TYPE_MAPPING[list(DISASTER_TYPE_MAPPING)[idx]]
            elif dname in dtype_vals:
                idx = dtype_vals.index(dname)
                disaster_name = list(DISASTER_TYPE_MAPPING.values())[idx]
            else:
                disaster_name = 'Other'
            dtype = DisasterType.objects.get(name=disaster_name)

            # get the country mapping
            iso_code = r['GEC_code']
            if len(iso_code) == 2:
                country = Country.objects.filter(iso=iso_code.lower())
            else:
                country = Country.objects.filter(name=r['GEC_code'])
            if country.count() == 0:
                country = None
            else:
                country = country.first()

            # get the region mapping, using the country if possible
            if country is not None and country.region is not None:
                region = Region.objects.get(pk=country.region.pk)
            else:
                regions = {'africa': 0, 'americas': 1, 'asia pacific': 2, 'europe': 3, 'middle east and north africa': 4}
                region_name = r['OSR_name'].lower().strip()
                if not region_name in regions:
                    region = None
                else:
                    region = Region.objects.get(name=regions[region_name])

            # get the most recent appeal detail, using the appeal start date
            # if there is more than one detail, the start date should be the *earliest
            if len(r['Details']) == 1:
                detail = r['Details'][0]
                start_date = self.parse_date(detail['APD_startDate'])
            else:
                details = sorted(r['Details'], reverse=True, key=lambda x: self.parse_date(x['APD_startDate']))
                detail = details[0]
                start_date = self.parse_date(details[-1]['APD_startDate'])

            atypes = {66: AppealType.DREF, 64: AppealType.APPEAL, 1537: AppealType.INTL}
            atype = atypes[detail['APD_TYP_Id']]

            if atype == AppealType.DREF:
                # appeals are always fully-funded
                amount_funded = detail['APD_amountCHF']
            else:
                amount_funded = 0 if detail['ContributionAmount'] is None else detail['ContributionAmount']

            end_date = self.parse_date(detail['APD_endDate'])
            # for open appeals, if we have a country, try to guess what emergency it belongs to.
            # only consider emergencies within the past 90 days
            event = None
            if country is not None and end_date > datetime.utcnow().replace(tzinfo=timezone.utc):
                six_mos = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=90)
                event = Event.objects.exclude(created_at__lt=six_mos).filter(countries__in=[country]).filter(dtype=dtype).order_by('-created_at')
                if event.count():
                    event = event.first()
                else:
                    event = None

            fields = {
                'aid': r['APP_Id'],
                'name': r['APP_name'],
                'dtype': dtype,
                'atype': atype,

                'country': country,
                'region': region,

                'sector': r['OSS_name'],
                'code': r['APP_code'],
                'status': {'Active': 0, 'Closed': 1, 'Frozen': 2, 'Archived': 3}[r['APP_status']],

                'start_date': start_date,
                'end_date': end_date,
                'num_beneficiaries': detail['APD_noBeneficiaries'],
                'amount_requested': detail['APD_amountCHF'],
                'amount_funded': amount_funded,
            }
            if event is not None:
                fields['event'] = event
                fields['unconfirmed_event'] = True

            appeal, created = Appeal.objects.update_or_create(code=fields['code'], defaults=fields)
            if created:
                num_created = created + 1
            else:
                num_updated = updated + 1

        print('%s appeals created' % num_created)
        print('%s appeals updated' % num_updated)
        print('%s total appeals' % Appeal.objects.all().count())
