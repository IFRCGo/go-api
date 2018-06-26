import os
import csv
import subprocess
import pytz
from django.utils import timezone
from datetime import datetime, timedelta
from glob import glob
from ftplib import FTP
from zipfile import ZipFile
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from api.models import (
    DisasterType,
    Country,
    FieldReport,
    Action,
    ActionsTaken,
    FieldReportContact,
    SourceType,
    Source,
    Event,
)
from api.fixtures.dtype_map import PK_MAP
from api.event_sources import SOURCES
from api.logger import logger

REPORT_DATE_FORMAT = '%m/%d/%y %H:%M:%S'

def extract_table(dbfile, table):
    """ Extract a table from the Access database """
    cmd = 'mdb-export %s %s' % (dbfile, table)
    try:
        output = subprocess.check_output(cmd.split(' ')).splitlines()
    except Exception as e:
        logger.error(e)
    output = [o.decode('utf-8') for o in output]
    reader = csv.reader(output, delimiter=',', quotechar='"')
    records = []
    for i, row in enumerate(reader):
        if i == 0:
            header = row
        else:
            d = {header[i]: l for i, l in enumerate(row)}
            records.append(d)
    return records


def contact_is_valid(contact, field):
    for suffix in ['Name', 'Function', 'Contact']:
        if contact['%s%s' % (field, suffix)] is None:
            return False
    return True


def get_dbfile():
    ftphost = os.environ.get('GO_FTPHOST', None)
    ftpuser = os.environ.get('GO_FTPUSER', None)
    ftppass = os.environ.get('GO_FTPPASS', None)
    dbpass = os.environ.get('GO_DBPASS', None)
    if ftphost is None or ftpuser is None or ftppass is None:
        if os.path.exists('URLs.mdb'):
            logger.info('No credentials in env, using local MDB database file')
            logger.warn('If this occurs outside development, contact an administrator')
            return 'URLs.mdb'
        else:
            raise Exception('FTP credentials not provided (GO_FTPHOST, GO_FTPUSER, GO_FTPPASS)')
    if dbpass is None:
        raise Exception('Database encryption password not provided (GO_DBPASS)')
    logger.info('Attempting connection to FTP')
    ftp = FTP(ftphost)
    ftp.login(user=ftpuser, passwd=ftppass)
    ftp.cwd('/dmis/')
    data = []
    ftp.dir('-t', data.append)
    filename = data[-1].split()[3]

    # check if we already have this file
    files = glob('URLs*zip')
    if filename in files and os.path.exists('URLs.mdb'):
        ftp.quit()
        return 'URLs.mdb'

    # clean up old files
    for f in files:
        os.remove(f)

    logger.info('Fetching %s' % filename)
    with open(filename, 'wb') as f:
        ftp.retrbinary('RETR ' + filename, f.write, 2014)
    ftp.quit()

    logger.info('Unzipping database file')
    zp = ZipFile(filename)
    zp.extractall('./', pwd=dbpass.encode('cp850', 'replace'))
    return 'URLs.mdb'


def fetch_relation(records, rid):
    """ Find record with matching ReportID to rid """
    matches = [r for r in records if r['ReportID'] == rid]
    results = []
    for match in matches:
        results.append({key: (value if value != '' else None) for key, value in match.items()})
    return results


class Command(BaseCommand):
    help = 'Add new entries from Access database file'

    def handle(self, *args, **options):
        # get latest
        filename = get_dbfile()

        # numeric details records
        details_rc = extract_table(filename, 'EW_Report_NumericDetails')
        # check for 1 record for each field report
        fids = [r['ReportID'] for r in details_rc]
        if len(set(fids)) != len(fids):
            raise Exception('More than one NumericDetails record for a field report')
        # numeric details records
        details_gov = extract_table(filename, 'EW_Report_NumericDetails_GOV')
        # check for 1 record for each field report
        fids = [r['ReportID'] for r in details_gov]
        if len(set(fids)) != len(fids):
            raise Exception('More than one NumericDetails record for a field report')

        # information
        info_table = extract_table(filename, 'EW_Report_InformationManagement')
        fids = [r['ReportID'] for r in info_table]
        if len(set(fids)) != len(fids):
            raise Exception('More than one InformationManagement record for a field report')

        ### many-to-many

        # actions taken
        actions_national = extract_table(filename, 'EW_Report_ActionTakenByRedCross')
        actions_foreign = extract_table(filename, 'EW_Report_ActionTakenByPnsRC')
        actions_federation = extract_table(filename, 'EW_Report_ActionTakenByFederationRC')

        # source types
        source_types = extract_table(filename, 'EW_lofSources')
        for s in source_types:
            SourceType.objects.get_or_create(pk=s['SourceID'], defaults={'name': s['SourceName']})

        source_table = extract_table(filename, 'EW_Reports_Sources')

        # disaster response
        dr_table = extract_table(filename, 'EW_DisasterResponseTools')
        # check for 1 record for each field report
        fids = [r['ReportID'] for r in dr_table]
        if len(set(fids)) != len(fids):
            raise Exception('More than one DisasterResponseTools record for a field report')

        # contacts
        contacts = extract_table(filename, 'EW_Report_Contacts')

        # field report
        reports = extract_table(filename, 'EW_Reports')
        rids = [r.rid for r in FieldReport.objects.all()]
        num_reports_created = 0
        logger.info('%s reports in database' % len(reports))
        for i, report in enumerate(reports):

            # Skip reports that we've already ingested.
            # We don't have to update them because field reports can't be updated in DMIS.
            rid = report['ReportID']
            if rid in rids:
                continue

            report_name = report['Summary']
            report_description = report['BriefSummary']
            report_dtype = DisasterType.objects.get(pk=PK_MAP[report['DisasterTypeID']])
            record = {
                'rid': rid,
                'summary': report_name,
                'description': report_description,
                'dtype': report_dtype,
                'status': report['StatusID'],
                'request_assistance': report['GovRequestsInternAssistance'],
                'actions_others': report['ActionTakenByOthers'],
                'report_date': datetime.strptime(report['Inserted'], REPORT_DATE_FORMAT).replace(tzinfo=pytz.utc),
            }
            details = fetch_relation(details_rc, report['ReportID'])
            assert(len(details) <= 1)
            if len(details) > 0:
                details = details[0]
                record.update({
                    'num_injured': details['NumberOfInjured'],
                    'num_dead': details['NumberOfCasualties'],
                    'num_missing': details['NumberOfMissing'],
                    'num_affected': details['NumberOfAffected'],
                    'num_displaced': details['NumberOfDisplaced'],
                    'num_assisted': details['NumberOfAssistedByRC'],
                    'num_localstaff': details['NumberOfLocalStaffInvolved'],
                    'num_volunteers': details['NumberOfVolunteersInvolved'],
                    'num_expats_delegates': details['NumberOfExpatsDelegates']
                })
            details = fetch_relation(details_gov, report['ReportID'])
            assert(len(details) <= 1)
            if len(details) > 0:
                details = details[0]
                record.update({
                    'gov_num_injured': details['NumberOfInjured_GOV'],
                    'gov_num_dead': details['NumberOfDead_GOV'],
                    'gov_num_missing': details['NumberOfMissing_GOV'],
                    'gov_num_affected': details['NumberOfAffected_GOV'],
                    'gov_num_displaced': details['NumberOfDisplaced_GOV'],
                    'gov_num_assisted': details['NumberOfAssistedByGov_GOV']
                })
            info = fetch_relation(info_table, report['ReportID'])
            if len(info) > 0:
                info = {k: '' if v is None else v for k, v in info[0].items()}
                record.update({
                    'bulletin': {'': 0, 'None': 0, 'Planned': 2, 'Published': 3}[info['InformationBulletin']],
                    'dref': {'': 0, 'No': 0, 'Planned': 2, 'Yes': 3}[info['DREFRequested']],
                    'dref_amount': 0 if info['DREFRequestedAmount'] == '' else float(info['DREFRequestedAmount']),
                    'appeal': {'': 0, 'Planned': 2, 'Yes': 3, 'NB': 0, 'No': 0, 'YES': 3}[info['EmergencyAppeal']],
                    'appeal_amount': 0 if info['EmergencyAppealAmount'] == '' else float(info['EmergencyAppealAmount']),
                })
            # disaster response
            response = fetch_relation(dr_table, report['ReportID'])

            if len(response) > 0:
                response = {k: '' if v is None else v for k, v in response[0].items()}
                record.update({
                    'rdrt': {'': 0, 'No': 0, 'Yes': 3, 'Planned/Requested': 2}[response['RDRT']],
                    'fact': {'': 0, 'No': 0, 'Yes': 3, 'Planned/Requested': 2}[response['FACT']],
                    'eru_relief': {'': 0, 'Yes': 3, 'Planned/Requested': 2, 'No': 0}[response['ERU']]
                })

            field_report = FieldReport(**record)

            # Create an associated event object
            event_record = {
                'name': report_name if len(report_name) else report_dtype.name,
                'summary': report_description,
                'dtype': report_dtype,
                'disaster_start_date': datetime.utcnow().replace(tzinfo=timezone.utc),
                'auto_generated': True,
                'auto_generated_source': SOURCES['report_ingest'],
            }
            event = Event(**event_record)
            event.save()

            logger.info('Adding %s' % report_name)
            field_report.event = event
            field_report.save()
            num_reports_created = num_reports_created + 1

            try:
                country = Country.objects.select_related().get(pk=report['CountryID'])
            except ObjectDoesNotExist:
                logger.warn('Could not find a matching country for %s' % report['CountryID'])
                country = None

            if country is not None:
                field_report.countries.add(country)
                event.countries.add(country)
                if country.region is not None:
                    # No need to add a field report region, as that happens through a trigger.
                    field_report.regions.add(country.region)
                    event.regions.add(country.region)

            ### add items with foreignkeys to report
            # national red cross actions
            actions = fetch_relation(actions_national, report['ReportID'])
            if len(actions) > 0:
                txt = ' '.join([a['Value'] for a in actions if a['Value'] is not None])
                act = ActionsTaken(organization='NTLS', summary=txt, field_report=field_report)
                act.save()
                for pk in [a['ActionTakenByRedCrossID'] for a in actions]:
                    act.actions.add(*Action.objects.filter(pk=pk))

            # foreign red cross actions
            actions = fetch_relation(actions_foreign, report['ReportID'])
            if len(actions) > 0:
                txt = ' '.join([a['Value'] for a in actions if a['Value'] is not None])
                act = ActionsTaken(organization='PNS', summary=txt, field_report=field_report)
                act.save()
                for pk in [a['ActionTakenByRedCrossID'] for a in actions]:
                    act.actions.add(*Action.objects.filter(pk=pk))

            # federation red cross actions
            actions = fetch_relation(actions_federation, report['ReportID'])
            if len(actions) > 0:
                txt = ' '.join([a['Value'] for a in actions if a['Value'] is not None])
                act = ActionsTaken(organization='FDRN', summary=txt, field_report=field_report)
                act.save()
                for pk in [a['ActionTakenByRedCrossID'] for a in actions]:
                    act.actions.add(*Action.objects.filter(pk=pk))

            # sources
            sources = fetch_relation(source_table, report['ReportID'])
            for s in sources:
                spec = '' if s['Specification'] is None else s['Specification']
                src = Source.objects.create(stype=SourceType.objects.get(pk=s['SourceID']),
                                            spec=spec, field_report=field_report)

            # disaster response
            response = fetch_relation(dr_table, report['ReportID'])

            # contacts
            contact = fetch_relation(contacts, report['ReportID'])
            if len(contact) > 0:
                # make sure just one contacts record
                assert(len(contact) == 1)
                contact = contact[0]
                fields = ['Originator', 'Primary', 'Federation', 'NationalSociety', 'MediaNationalSociety', 'Media']
                for f in fields:
                    if contact_is_valid(contact, f):
                        ct = FieldReportContact.objects.create(
                            ctype=f,
                            name=contact['%sName' % f],
                            title=contact['%sFunction' % f],
                            email=contact['%sContact' % f],
                            field_report=field_report,
                        )
        total_reports = FieldReport.objects.all()
        logger.info('%s reports created' % num_reports_created)
        logger.info('%s reports in database' % total_reports.count())

        # org type mapping
        org_types = {
            '1': 'NTLS',
            '2': 'DLGN',
            '3': 'SCRT',
            '4': 'ICRC',
        }
        last_login_threshold = timezone.now() - timedelta(days=365)

        # add users
        user_records = extract_table(filename, 'DMISUsers')
        processed_users = 0
        for i, user_data in enumerate(user_records):
            if user_data['LoginLastSuccess'] == '':
                continue

            last_login = datetime.strptime(user_data['LoginLastSuccess'], REPORT_DATE_FORMAT,)
            last_login = pytz.UTC.localize(last_login)

            # skip users who haven't logged in for a year
            if last_login < last_login_threshold:
                continue

            try:
                user = User.objects.get(username=user_data['UserName'])
            except ObjectDoesNotExist:
                user = None

            if user is None:
                name = user_data['RealName'].split()
                first_name = name[0]
                last_name = ' '.join(name[1:]) if len(name) > 1 else ''
                user = User.objects.create(username=user_data['UserName'],
                                           first_name=first_name if len(first_name) <= 30 else '',
                                           last_name=last_name if len(last_name) <= 30 else '',
                                           email=user_data['EmailAddress'],
                                           last_login=last_login,
                                           )
                user.set_password(user_data['Password'])
                user.is_staff = True if user_data['UserIsSysAdm'] == '1' else False

            # set user profile info
            user.profile.org = user_data['OrgTypeSpec'] if len(user_data['OrgTypeSpec']) <= 100 else ''
            user.profile.org_type = org_types.get(user_data['OrgTypeID'])
            user.profile.country = Country.objects.get(pk=user_data['CountryID'])
            user.profile.city = user_data['City'] if len(user_data['City']) <= 100 else ''
            user.profile.department = user_data['Department'] if len(user_data['Department']) <= 100 else ''
            user.profile.position = user_data['Position'] if len(user_data['Position']) <= 100 else ''
            user.profile.phone_number = user_data['PhoneNumberProf'] if len(user_data['PhoneNumberProf']) <= 100 else ''
            user.save()
            processed_users = processed_users + 1
        logger.info('%s updated active user records' % len(processed_users))
