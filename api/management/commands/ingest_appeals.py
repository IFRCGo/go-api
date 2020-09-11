import os
import json
from requests import Session, exceptions as reqexc
from requests.adapters import HTTPAdapter
from datetime import datetime, timezone, timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone as tz
from api.models import AppealType, Appeal, Region, Country, DisasterType, Event, CronJobStatus
from api.fixtures.dtype_map import DISASTER_TYPE_MAPPING
from api.logger import logger
from api.create_cron import create_cron_record

CRON_NAME = 'ingest_appeals'
DTYPE_KEYS = [a.lower() for a in DISASTER_TYPE_MAPPING.keys()]
DTYPE_VALS = [a.lower() for a in DISASTER_TYPE_MAPPING.values()]
REGION_TO_COUNTRY = {
    'JAK': 'ID',  # Jakarta Country Cluster Office: Indonesia
    'SAM': 'AR',  # South Cone and Brazil Country Cluster Office: Argentina
    'TEG': 'HN',  # Tegucigalpa Country Cluster Office: Honduras
    'AFR': 'KE',  # Africa regional office: Kenya
    'EAF': 'KE',  # Eastern Africa country cluster: Kenya
    'WAF': 'NG',  # Western Africa country cluster: Nigeria
    'CAF': 'CM',  # Central Africa country cluster: Cameroon
    'SAF': 'ZA',  # Southern Africa country cluster: South Africa
    'CAM': 'HT',  # Latin Caribbean Country Cluster Office: Haiti
    'CAR': 'TT',  # Caribbean Country Cluster: Trinidad and Tobago
    'NAM': 'PA',  # Americas regional office: Panama
    'AME': 'PA',  # Americas regional office: Panama
    'ASI': 'MY',  # Asia Pacific regional office / New Delhi country cluster: Malaysia
    'EEU': 'HU',  # Europe Regional Office: Hungary
    'EUR': 'HU',  # Europe Regional Office: Hungary
    'WEU': 'CH',  # (Western) Europe regional office: Switzerland
    'NAF': 'TN',  # MENA regional office / Tunis country cluster: Tunisia
    'MEA': 'GE',  # MENA Regonal Office / Southern Caucasus country cluster: Georgia
    'OCE': 'FJ',  # Suva Country Cluster Office: Fiji
    'WAF': 'SG',  # Sahel country cluster: Senegal
    'WRD': 'CH',  # IFRC Headquarters: Switzerland
    'SAM': 'PE',  # Andean Country Cluster Office: Peru
    'SEA': 'TH',  # Bangkok Country Cluster Office: Thailand
    'SAS': 'IN',  # Southern Asia Country Cluster Office: India
    'EAS': 'CN',  # Beijing Country Cluster Office: China
    'CAS': 'KZ',  # Central Asia country cluster: Kazakhstan
    'HK': 'CN',  # Hong Kong: China
    'TW': 'CN',  # Taiwan: China
    'XK': 'RS',  # Kosovo: Serbia
}


class Command(BaseCommand):
    help = 'Add new entries from Access database file'

    def parse_date(self, date_string):
        timeformat = '%Y-%m-%dT%H:%M:%S'
        return datetime.strptime(date_string[:18], timeformat).replace(tzinfo=timezone.utc)

    def create_bilaterals_dict(self, records):
        ''' Aggregate amounts (rec['AmountCHF']) of Bilateral records '''
        bilaterals = {}
        for rec in records:
            if rec['APP_Code'] and rec['AmountCHF']:
                if rec['APP_Code'] in bilaterals.keys():
                    bilaterals[rec['APP_Code']] += rec['AmountCHF']
                else:
                    bilaterals[rec['APP_Code']] = rec['AmountCHF']
        return bilaterals

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
                bilaterals = self.create_bilaterals_dict(records)
        else:
            # get latest BILATERALS
            logger.info('Querying appeals API for new appeals data')
            url = 'http://go-api.ifrc.org/api/appealbilaterals'
            auth = (os.getenv('APPEALS_USER'), os.getenv('APPEALS_PASS'))
            adapter = HTTPAdapter(max_retries=settings.RETRY_STRATEGY)
            sess = Session()
            sess.mount('http://', adapter)

            # try 3 times to reach the API
            try:
                response = sess.get(url, auth=auth)
            except reqexc.HTTPError as ex:
                log_text = f'Error querying AppealBilaterals API: {ex}'
                logger.error(log_text)
                create_cron_record(CRON_NAME, log_text, CronJobStatus.ERRONEOUS)
                return
            except Exception as ex:
                log_text = f'Error querying AppealBilaterals API at {url}: {str(ex)}'
                logger.error(log_text)
                create_cron_record(CRON_NAME, log_text, CronJobStatus.ERRONEOUS)
                return
            records = response.json()
            bilaterals = self.create_bilaterals_dict(records)

            # write the current record file to local disk
            with open('appealbilaterals.json', 'w') as outfile:
                json.dump(records, outfile)

            # get latest APPEALS
            logger.info('Querying appeals API for new appeals data')
            url = 'http://go-api.ifrc.org/api/appeals'
            # try 3 times to reach the API
            try:
                response = sess.get(url, auth=auth)
            except reqexc.HTTPError as ex:
                log_text = f'Error querying Appeals API: {ex}'
                logger.error(log_text)
                create_cron_record(CRON_NAME, log_text, CronJobStatus.ERRONEOUS)
                return
            except Exception as ex:
                log_text = f'Error querying Appeals API at {url}: {str(ex)}'
                logger.error(log_text)
                create_cron_record(CRON_NAME, log_text, CronJobStatus.ERRONEOUS)
                return

            records = response.json()

            # write the current record file to local disk
            with open('appeals.json', 'w') as outfile:
                json.dump(records, outfile)

            codes = Appeal.objects.values_list('code', flat=True)
            for r in records:
                # Temporary filtering, the manual version should be kept:
                if r['APP_code'] in ['MDR65002', 'MDR00001', 'MDR00004']:
                    continue
                if r['APP_code'] not in codes:
                    new.append(r)
                else:
                    # We use all records, do NOT check if last_modified > since_last_checked
                    modified.append(r)

        return new, modified, bilaterals

    def parse_disaster_name(self, dname):
        if dname in DTYPE_KEYS:
            idx = DTYPE_KEYS.index(dname)
            disaster_name = DISASTER_TYPE_MAPPING[list(DISASTER_TYPE_MAPPING)[idx]]
        elif dname in DTYPE_VALS:
            idx = DTYPE_VALS.index(dname)
            disaster_name = list(DISASTER_TYPE_MAPPING.values())[idx]
        else:
            disaster_name = 'Other'
        dtype = DisasterType.objects.get(name=disaster_name)
        return dtype

    def parse_country(self, region_code, country_name):
        country = None
        iso_code = None
        if region_code in REGION_TO_COUNTRY:
            iso_code = REGION_TO_COUNTRY[region_code]

        if iso_code:
            country = Country.objects.filter(iso__iexact=iso_code).first()
        else:
            country = Country.objects.filter(name__iexact=country_name).first()

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
            regions = {
                'africa': 0,
                'americas': 1,
                'asia pacific': 2,
                'europe': 3,
                'middle east and north africa': 4
            }
            region_name = r['OSR_name'].lower().strip()
            if region_name not in regions:
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
        if options['is_new_appeal'] and country is not None and end_date > tz.now():
            six_mos = tz.now() - timedelta(days=90)
            event = (
                Event.objects.exclude(created_at__lt=six_mos)
                             .filter(countries__in=[country])
                             .filter(dtype=dtype)
                             .order_by('-created_at')
                             .first()
            )

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
        start_appeals_count = Appeal.objects.all().count()
        try:
            new, modified, bilaterals = self.get_new_or_modified_appeals()
        except Exception as ex:
            logger.error(f'Getting Appeals and AppealBilaterals failed: {str(ex)}')
            return
        logger.info(f'{start_appeals_count} current appeals')
        logger.info(f'Creating {len(new)} new appeals')
        logger.info(f'Updating {len(modified)} existing appeals that MIGHT have been modified')

        errors = []
        num_created = 0
        for i, r in enumerate(new):
            fields = self.parse_appeal_record(r, is_new_appeal=True)
            # correction of the appeal record with appealbilaterals value
            if fields['code'] in bilaterals:
                fields['amount_funded'] += round(bilaterals[fields['code']], 1)
            try:
                Appeal.objects.create(**fields)
                num_created += 1
            except Exception as ex:
                err_text = f'Could not create appeal with code {fields["code"]}'
                logger.error(str(ex)[:100])
                logger.error(err_text)
                errors.append(err_text)

        num_updated = 0
        for i, r in enumerate(modified):
            fields = self.parse_appeal_record(r, is_new_appeal=False)
            # correction of the appeal record with appealbilaterals value
            if fields['code'] in bilaterals:
                fields['amount_funded'] += round(bilaterals[fields['code']], 1)

            try:
                appeal, created = Appeal.objects.update_or_create(code=fields['code'], defaults=fields)
                num_updated += 1
            except Exception as ex:
                err_text = f'Could not update appeal with code {fields["code"]}'
                logger.error(str(ex)[:100])
                logger.error(err_text)
                errors.append(err_text)

        if errors:
            create_cron_record(CRON_NAME, '\n'.join(errors), CronJobStatus.WARNED, len(errors))

        appeals_count = Appeal.objects.all().count()
        logger.info(f'{num_created} appeals created')
        logger.info(f'{num_updated} appeals updated')
        logger.info(f'{appeals_count} total appeals')
        logger.info('Appeals ingest completed')

        cron_msg = f'Start appeals count {start_appeals_count}\nAppeals ingest completed, \
                    {appeals_count} total appeals ({num_created} new, {num_updated} existing).'
        create_cron_record(CRON_NAME, cron_msg, CronJobStatus.SUCCESSFUL, appeals_count)
