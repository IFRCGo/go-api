import os
import csv
import logging
import subprocess
import pytz
from django.utils import timezone
from datetime import datetime, timedelta
from glob import glob
from ftplib import FTP
from zipfile import ZipFile
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import DisasterType, Country, FieldReport


def extract_table(dbfile, table):
    """ Extract a table from the Access database """
    cmd = 'mdb-export %s %s' % (dbfile, table)
    try:
        output = subprocess.check_output(cmd.split(' ')).splitlines()
    except Exception as e:
        logging.error(e)
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


def get_dbfile():
    ftphost = os.environ.get('GO_FTPHOST', None)
    ftpuser = os.environ.get('GO_FTPUSER', None)
    ftppass = os.environ.get('GO_FTPPASS', None)
    dbpass = os.environ.get('GO_DBPASS', None)
    if ftphost is None or ftpuser is None or ftppass is None:
        raise Exception('FTP credentials not provided (GO_FTPHOST, GO_FTPUSER, GO_FTPPASS)')
    if dbpass is None:
        raise Exception('Database encryption password not provided (GO_DBPASS)')
    print('Connecting to FTP')
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

    print('Fetching %s' % filename)
    with open(filename, 'wb') as f:
        ftp.retrbinary('RETR ' + filename, f.write, 2014)
    ftp.quit()

    print('Unzipping database file')
    zp = ZipFile(filename)
    zp.extractall('./', pwd=dbpass.encode('cp850', 'replace'))
    return 'URLs.mdb'


def fetch_relation(records, rid):
    """ Find record with matching ReportID to rid """
    result = [r for r in records if r['ReportID'] == rid]
    assert(len(result) <= 1)
    if len(result) == 1:
        return {key: (value if value != '' else None) for key, value in result[0].items()}
    else:
        return {}


class Command(BaseCommand):
    help = 'Add new entries from Access database file'

    def handle(self, *args, **options):
        # get latest
        filename = get_dbfile()

        # disaster response records
        dr_records = extract_table(filename, 'EW_DisasterResponseTools')
        # check for 1 record for each field report
        fids = [r['ReportID'] for r in dr_records]
        if len(set(fids)) != len(fids):
            raise Exception('More than one DisasterResponseTools record for a field report')

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

        # actions taken
        actions_national = extract_table(filename, 'EW_Report_ActionTakenByRedCross')
        actions_foreign = extract_table(filename, 'EW_Report_ActionTakenByPnsRC')
        actions_federation = extract_table(filename, 'EW_Report_ActionTakenByFederationRC')

        # contacts
        contacts = extract_table(filename, 'EW_Report_Contacts')

        reports = extract_table(filename, 'EW_Reports')
        rids = [r.rid for r in FieldReport.objects.all()]
        print('%s reports in database' % len(reports))
        for i, report in enumerate(reports):
            if report['ReportID'] in rids:
                continue
            print(i) if (i % 100) == 0 else None
            record = {
                'rid': report['ReportID'],
                'summary': report['Summary'],
                'description': report['BriefSummary'],
                'dtype': DisasterType.objects.get(pk=report['DisasterTypeID']),
                'status': report['StatusID'],
                'request_assistance': report['GovRequestsInternAssistance'],
                'action': report['ActionTaken']
            }
            details = fetch_relation(details_rc, report['ReportID'])
            if len(details) > 1:
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
            if len(details) > 1:
                record.update({
                    'gov_num_injured': details['NumberOfInjured_GOV'],
                    'gov_num_dead': details['NumberOfDead_GOV'],
                    'gov_num_missing': details['NumberOfMissing_GOV'],
                    'gov_num_affected': details['NumberOfAffected_GOV'],
                    'gov_num_displaced': details['NumberOfDisplaced_GOV'],
                    'gov_num_assisted': details['NumberOfAssistedByGov_GOV']
                })

            # actions taken
            actions = fetch_relation(actions_national, report['ReportID'])
            if len(actions) > 1:
                record.update({
                    'actions_national': actions['Value']
                })
            actions = fetch_relation(actions_foreign, report['ReportID'])
            if len(actions) > 1:
                record.update({
                    'actions_foreign': actions['Value']
                })
            actions = fetch_relation(actions_federation, report['ReportID'])
            if len(actions) > 1:
                record.update({
                    'actions_federation': actions['Value']
                })

            contact = fetch_relation(contacts, report['ReportID'])
            # add contacts here

            item = FieldReport(**record)
            item.save()
            item.countries.add(*Country.objects.filter(pk=report['CountryID']))

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
        print('%s users in database' % len(user_records))
        for i, user_data in enumerate(user_records):
            if user_data['LoginLastSuccess'] == '':
                continue

            last_login = datetime.strptime(user_data['LoginLastSuccess'],
                                           '%m/%d/%y %H:%M:%S',
                                           )
            last_login = pytz.UTC.localize(last_login)

            # skip users who haven't logged in for a year
            if last_login < last_login_threshold:
                continue

            try:
                user = User.objects.get(username=user_data['UserName'])
            except User.DoesNotExist:
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
                print(i) if (i % 100) == 0 else None

            # set user profile info
            user.profile.org = user_data['OrgTypeSpec'] if len(user_data['OrgTypeSpec']) <= 100 else ''
            user.profile.org_type = org_types.get(user_data['OrgTypeID'])
            user.profile.country = Country.objects.get(pk=user_data['CountryID'])
            user.profile.city = user_data['City'] if len(user_data['City']) <= 100 else ''
            user.profile.department = user_data['Department'] if len(user_data['Department']) <= 100 else ''
            user.profile.position = user_data['Position'] if len(user_data['Position']) <= 100 else ''
            user.profile.phone_number = user_data['PhoneNumberProf'] if len(user_data['PhoneNumberProf']) <= 100 else ''

            user.set_password(user_data['Password'])
            user.is_staff = True if user_data['UserIsSysAdm'] == '1' else False
            user.save()

        items = FieldReport.objects.all()
        print('%s items' % items.count())
