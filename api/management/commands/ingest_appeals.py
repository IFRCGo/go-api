import os
import sys
import requests
import json
from datetime import datetime, timezone, timedelta
from django.core.management.base import BaseCommand
from api.models import AppealType, AppealStatus, Appeal, Region, Country, DisasterType, Event, CronJob, CronJobStatus
from api.fixtures.dtype_map import DISASTER_TYPE_MAPPING
from api.logger import logger

dtype_keys = [a.lower() for a in DISASTER_TYPE_MAPPING.keys()]
dtype_vals = [a.lower() for a in DISASTER_TYPE_MAPPING.values()]
region2country = {'JAK': 'ID', #Jakarta Country Cluster Office: Indonesia
                  'SAM': 'AR', #South Cone and Brazil Country Cluster Office: Argentina
                  'TEG': 'HN', #Tegucigalpa Country Cluster Office: Honduras
                  'AFR': 'KE', #Africa regional office: Kenya
                  'EAF': 'KE', #Eastern Africa country cluster: Kenya
                  'WAF': 'NG', #Western Africa country cluster: Nigeria
                  'CAF': 'CM', #Central Africa country cluster: Cameroon
                  'SAF': 'ZA', #Southern Africa country cluster: South Africa
                  'CAM': 'HT', #Latin Caribbean Country Cluster Office: Haiti
                  'CAR': 'TT', #Caribbean Country Cluster: Trinidad and Tobago
                  'NAM': 'PA', #Americas regional office: Panama
                  'AME': 'PA', #Americas regional office: Panama
                  'ASI': 'MY', #Asia Pacific regional office / New Delhi country cluster: Malaysia
                  'EEU': 'HU', #Europe Regional Office: Hungary
                  'EUR': 'HU', #Europe Regional Office: Hungary
                  'WEU': 'CH', #(Western) Europe regional office: Switzerland
                  'NAF': 'TN', #MENA regional office / Tunis country cluster: Tunisia
                  'MEA': 'GE', #MENA Regonal Office / Southern Caucasus country cluster: Georgia
                  'OCE': 'FJ', #Suva Country Cluster Office: Fiji
                  'WAF': 'SG', #Sahel country cluster: Senegal
                  'WRD': 'CH', #IFRC Headquarters: Switzerland
                  'SAM': 'PE', #Andean Country Cluster Office: Peru
                  'SEA': 'TH', #Bangkok Country Cluster Office: Thailand
                  'SAS': 'IN', #Southern Asia Country Cluster Office: India
                  'EAS': 'CN', #Beijing Country Cluster Office: China
                  'CAS': 'KZ', #Central Asia country cluster: Kazakhstan
                  'HK':  'CN', #Hong Kong: China
                  'TW':  'CN', #Taiwan: China
                  'XK':  'RS', #Kosovo: Serbia
}

class Command(BaseCommand):
    help = 'Add new entries from Access database file'

    def parse_date(self, date_string):
        timeformat = '%Y-%m-%dT%H:%M:%S'
        return datetime.strptime(date_string[:18], timeformat).replace(tzinfo=timezone.utc)

    def get_new_or_modified_appeals(self):
        use_local_file = True if os.getenv('DJANGO_DB_NAME') == 'test' and os.path.exists('appeals.json') else False
        new = []
        modified = []
        if use_local_file:
            # read from static file for development
            logger.info('Using local appeals.json file')
            with open('appeals.json') as f:
                modified = json.loads(f.read())
            logger.info('Using local appealbilaterals.json file')
            with open('appealbilaterals.json') as f:
                records = json.loads(f.read())
                bilaterals = {}
                for r in records: # code duplication ¤
                    if r['APP_Code'] and r['AmountCHF']:
                        if r['APP_Code'] in bilaterals.keys():
                            bilaterals[r['APP_Code']] += r['AmountCHF']
                        else:
                            bilaterals[r['APP_Code']] = r['AmountCHF']
        else:
            # get latest BILATERALS
            logger.info('Querying appeals API for new appeals data')
            url = 'http://go-api.ifrc.org/api/appealbilaterals'
            auth = (os.getenv('APPEALS_USER'), os.getenv('APPEALS_PASS'))
            response = requests.get(url, auth=auth)
            if response.status_code != 200:
                text_to_log = 'Error querying AppealBilaterals API at ' + url
                logger.error(text_to_log)
                logger.error(response.content)
                body = { "name": "ingest_appeals", "message": text_to_log, "status": CronJobStatus.ERRONEOUS } # not every case is catched here, e.g. if the base URL is wrong...
                CronJob.sync_cron(body)
                raise Exception(text_to_log)

            records = response.json()

            # write the current record file to local disk
            with open('appealbilaterals.json', 'w') as outfile:
                json.dump(records, outfile)

            bilaterals = {}
            for r in records: # code duplication ¤
                if r['APP_Code'] and r['AmountCHF']:
                    if r['APP_Code'] in bilaterals.keys():
                        bilaterals[r['APP_Code']] += r['AmountCHF']
                    else:
                        bilaterals[r['APP_Code']] = r['AmountCHF']

            # get latest APPEALS
            logger.info('Querying appeals API for new appeals data')
            url = 'http://go-api.ifrc.org/api/appeals'
            auth = (os.getenv('APPEALS_USER'), os.getenv('APPEALS_PASS'))
            response = requests.get(url, auth=auth)
            if response.status_code != 200:
                logger.error('Error querying Appeals API')
                raise Exception('Error querying Appeals API')
            records = response.json()

            # write the current record file to local disk
            with open('appeals.json', 'w') as outfile:
                json.dump(records, outfile)

            codes = [a.code for a in Appeal.objects.all()]
            for r in records:
                # Temporary filtering, the manual version should be kept:
                if r['APP_code'] in ['MDR65002', 'MDR00001', 'MDR00004']:
                    continue
                #if r['APP_code'] != 'MDRMZ014': # Debug to test bilateral additions or other specific appeals
                #    continue
                if not r['APP_code'] in codes:
                    new.append(r)
                # We use all records, do NOT check if last_modified > since_last_checked
                modified.append(r)

        return new, modified, bilaterals

    def parse_disaster_name(self, dname):
        if dname in dtype_keys:
            idx = dtype_keys.index(dname)
            disaster_name = DISASTER_TYPE_MAPPING[list(DISASTER_TYPE_MAPPING)[idx]]
        elif dname in dtype_vals:
            idx = dtype_vals.index(dname)
            disaster_name = list(DISASTER_TYPE_MAPPING.values())[idx]
        else:
            disaster_name = 'Other'
        dtype = DisasterType.objects.get(name=disaster_name)
        return dtype

    def parse_country(self, iso_code, country_name):
        if iso_code in region2country:
            iso_code = region2country[iso_code]

        if len(iso_code) == 2:
            country = Country.objects.filter(iso=iso_code.lower())
        else:
            country = Country.objects.filter(name=country_name)

        if country.count() == 0:
            country = None
            #print(iso_code + ' ' + country_name) # Debug: for the "orphan" iso_codes
        else:
            country = country.first()
        return country

    def parse_appeal_record(self, r, **options):
        # get the disaster type mapping
        dname = '' if not r['ADT_name'] else r['ADT_name'].lower()
        # sometimes for some reason the string starts with a period
        if dname and dname[0] == '.':
            dname = dname[1:]
        dtype = self.parse_disaster_name(dname)

        # get the country mapping
        iso_code = r['GEC_code']
        country_name = r['OSC_name']
        country = self.parse_country(iso_code, country_name)

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
        # for new, open appeals, if we have a country, try to guess what emergency it belongs to.
        # only consider emergencies within the past 90 days
        event = None
        if options['is_new_appeal'] and country is not None and end_date > datetime.utcnow().replace(tzinfo=timezone.utc):
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
            fields['needs_confirmation'] = True

        return fields


    def handle(self, *args, **options):
        logger.info('Starting appeals ingest')
        new, modified, bilaterals = self.get_new_or_modified_appeals()
        logger.info('%s current appeals' % Appeal.objects.all().count())
        logger.info('Creating %s new appeals' % len(new))
        logger.info('Updating %s existing appeals that have been modified' % len(modified))

        num_created = 0
        for i, r in enumerate(new):
            fields = self.parse_appeal_record(r, is_new_appeal=True)
            if fields['code'] in bilaterals: # correction of the appeal record due to appealbilaterals api
                fields['amount_funded'] += round(bilaterals[fields['code']],1)
            try:
                Appeal.objects.create(**fields)
            except Exception as e:
                logger.error(str(e)[:100])
                logger.error('Could not create appeal with code %s' % fields['code'])
                continue
            num_created = num_created + 1

        num_updated = 0
        for i, r in enumerate(modified):
            fields = self.parse_appeal_record(r, is_new_appeal=False)
            if fields['code'] in bilaterals: # correction of the appeal record due to appealbilaterals api
                fields['amount_funded'] += round(bilaterals[fields['code']],1)

            try:
                appeal, created = Appeal.objects.update_or_create(code=fields['code'], defaults=fields)
            except Exception as e:
                logger.error(str(e)[:100])
                logger.error('Could not update appeal with code %s' % fields['code'])
                continue
            num_updated = num_updated + 1

        CronJobSum = Appeal.objects.all().count()
        logger.info('%s appeals created' % num_created)
        logger.info('%s appeals updated' % num_updated)
        logger.info('%s total appeals' % CronJobSum)
        logger.info('Appeals ingest completed')

        body = { "name": "ingest_appeals", "message": 'Appeals ingest completed, %s total appeals (%s new, %s existing).'
            % (CronJobSum, num_created, num_updated), "num_result": CronJobSum, "status": CronJobStatus.SUCCESSFUL }
        CronJob.sync_cron(body)
