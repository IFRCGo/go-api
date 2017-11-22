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
        nd_records = extract_table(filename, 'EW_Report_NumericDetails')
        # check for 1 record for each field report
        fids = [r['ReportID'] for r in nd_records]
        if len(set(fids)) != len(fids):
            raise Exception('More than one NumericDetails record for a field report')

        reports = extract_table(filename, 'EW_Reports')
        rids = [r.rid for r in FieldReport.objects.all()]
        print('%s reports in database' % len(reports))
        for i, report in enumerate(reports):
            if report['ReportID'] in rids:
                continue
            print(i) if (i % 100) == 0 else None
            nd = [r for r in nd_records if r['ReportID'] == report['ReportID']]
            assert(len(nd) <= 1)
            record = {
                'rid': report['ReportID'],
                'summary': report['Summary'],
                'description': report['BriefSummary'],
                'dtype': DisasterType.objects.get(pk=report['DisasterTypeID']),
                'status': report['StatusID'],
                'request_assistance': report['GovRequestsInternAssistance'],
                'action': report['ActionTaken']
            }
            if len(nd) == 1:
                nd = {key: (value if value != '' else None) for key, value in nd[0].items()}
                record.update({
                    'num_injured': nd['NumberOfInjured'],
                    'num_dead': nd['NumberOfCasualties'],
                    'num_missing': nd['NumberOfMissing'],
                    'num_affected': nd['NumberOfAffected'],
                    'num_displaced': nd['NumberOfDisplaced'],
                    'num_assisted_rc': nd['NumberOfAssistedByRC'],
                    'num_localstaff': nd['NumberOfLocalStaffInvolved'],
                    'num_volunteers': nd['NumberOfVolunteersInvolved'],
                    'num_expats_delegates': nd['NumberOfExpatsDelegates']
                })
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
                                           first_name=first_name,
                                           last_name=last_name,
                                           email=user_data['EmailAddress'],
                                           last_login=last_login,
                                           )
                print(i) if (i % 100) == 0 else None

            # set user profile info
            user.profile.org = user_data['OrgTypeSpec'] if len(user_data['OrgTypeSpec']) < 100 else ''
            user.profile.org_type = org_types.get(user_data['OrgTypeID'])
            user.profile.country = Country.objects.get(pk=user_data['CountryID'])
            user.profile.city = user_data['City']
            user.profile.department = user_data['Department']
            user.profile.position = user_data['Position'] if len(user_data['Position']) < 100 else ''
            user.profile.phone_number = user_data['PhoneNumberProf']

            user.set_password(user_data['Password'])
            user.is_staff = True if user_data['UserIsSysAdm'] == '1' else False
            user.save()

        items = FieldReport.objects.all()
        print('%s items' % items.count())
