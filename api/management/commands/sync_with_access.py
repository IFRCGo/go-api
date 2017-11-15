import os
import csv
import logging
import subprocess
from ftplib import FTP
from zipfile import ZipFile
from django.core.management.base import BaseCommand
from api.models import DisasterType, Country, FieldReport
from pdb import set_trace


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
    ftphost = os.environ.get('IFRC_FTPHOST', None)
    ftpuser = os.environ.get('IFRC_FTPUSER', None)
    ftppass = os.environ.get('IFRC_FTPPASS', None)
    print(ftphost, ftpuser, ftppass)
    if ftphost is None or ftpuser is None or ftppass is None:
        raise Exception('No FTP credentials provided (IFRC_FTPHOST, IFRC_FTPUSER, IFRC_FTPPASS)')
    print('Connecting to FTP')
    ftp = FTP(ftphost)
    ftp.login(user=ftpuser, passwd=ftppass)
    ftp.cwd('/dmis/')
    data = []
    ftp.dir('-t', data.append)
    filename = data[-1].split()[3]
    print('Fetching %s' % filename)
    with open(filename, 'wb') as f:
        ftp.retrbinary('RETR ' + filename, f.write, 2014)
    ftp.quit()
    print('Unzipping databae file')
    zp = ZipFile(filename)
    set_trace()
    zp.extractall('./', pwd=ftppass)
    os.remove(filename)
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

        items = FieldReport.objects.all()
        print('%s items' % items.count())
