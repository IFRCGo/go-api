import requests
from datetime import datetime, timezone
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from api.models import Appeal, AppealDocument
from deployments.models import ERU, PersonnelDeployment, Personnel, DeployedPerson
from api.logger import logger


class Command(BaseCommand):
    help = 'Ingest deployments'

    def parse_date(self, date_string):
        # 21Dec2017
        timeformat = '%d%b%Y'
        return datetime.strptime(date_string.strip(), timeformat).replace(tzinfo=timezone.utc)

    def handle(self, *args, **options):
        logger.info('Starting Deployment ingest')

        # url = 'https://proxy.hxlstandard.org/data.json?url=https%3A%2F%2Fdocs.google.com%2Fspreadsheets%2Fd%2F1CBvledFYc_uwlvHTvJE0SYS7_mPGU2L-zhrqbB4KNIA%2Fedit%23gid%3D0&header-row=1' # not enough.
        url = 'https://proxy.hxlstandard.org/data.json?tagger-match-all=on&' \
            + 'tagger-01-header=year&' \
            + 'tagger-01-tag=%23a1&' \
            + 'tagger-02-header=%2Aappeal+code&' \
            + 'tagger-02-tag=%23a2&' \
            + 'tagger-03-header=region&' \
            + 'tagger-03-tag=%23a3&' \
            + 'tagger-04-header=country&' \
            + 'tagger-04-tag=%23a4&' \
            + 'tagger-05-header=location&' \
            + 'tagger-05-tag=%23a5&' \
            + 'tagger-06-header=disaster+type&' \
            + 'tagger-06-tag=%23a6&' \
            + 'tagger-07-header=%2Adisaster+name&' \
            + 'tagger-07-tag=%23a7&' \
            + 'tagger-08-header=%2Aname&' \
            + 'tagger-08-tag=%23a8&' \
            + 'tagger-09-header=%2Adeploying+ns+%2F+ifrc+office&' \
            + 'tagger-09-tag=%23a9&' \
            + 'tagger-10-header=%2Agender&' \
            + 'tagger-10-tag=%23b1&' \
            + 'tagger-11-header=language&' \
            + 'tagger-11-tag=%23b2&' \
            + 'tagger-12-header=%2Aposition&' \
            + 'tagger-12-tag=%23b3&' \
            + 'tagger-13-header=%2Atype&' \
            + 'tagger-13-tag=%23b4&' \
            + 'tagger-14-header=supported+by+ns&' \
            + 'tagger-14-tag=%23b5&' \
            + 'tagger-15-header=availability&' \
            + 'tagger-15-tag=%23b6&' \
            + 'tagger-16-header=%2Aexp+start+date&' \
            + 'tagger-16-tag=%23b7&' \
            + 'tagger-17-header=%2Aexp+duration&' \
            + 'tagger-17-tag=%23b8&' \
            + 'tagger-18-header=%2Aalert&' \
            + 'tagger-18-tag=%23b9&' \
            + 'tagger-19-header=deployment+message&' \
            + 'tagger-19-tag=%23c1&' \
            + 'tagger-20-header=%2Astart+of+mission&' \
            + 'tagger-20-tag=%23c2&' \
            + 'tagger-21-header=%2Aend+of+mission&' \
            + 'tagger-21-tag=%23c3&' \
            + 'tagger-22-header=deployment+duration&' \
            + 'tagger-22-tag=%23c4&' \
            + 'tagger-23-header=deployed&' \
            + 'tagger-23-tag=%23c5&' \
            + 'tagger-24-header=rotation&' \
            + 'tagger-24-tag=%23c6&' \
            + 'tagger-25-header=comments&' \
            + 'tagger-25-tag=%23c7&' \
            + 'url=https%3A%2F%2Fdocs.google.com%2Fspreadsheets%2Fd%2F1CBvledFYc_uwlvHTvJE0SYS7_mPGU2L-zhrqbB4KNIA%2Fedit%23gid%3D0&' \
            + 'header-row=1'

        response = requests.get(url)
        if response.status_code != 200:
            logger.error('Error querying Deployment HXL API')
            raise Exception('Error querying Deployment HXL API')
        records = response.json()

        # some logging variables
        not_found = []
        existing = []
        created = []

        columns = [a.replace('*','').replace(' ','') for a in records[0]]
        # ['Year', 'AppealCode', 'Region', 'Country', 'Location', 'Disastertype', 'Disastername', 'Name', 'DeployingNS/IFRCOffice', 'Gender', 'Language', 'Position', 'Type', 'SupportedbyNS', 'Availability', 'Expstartdate', 'expduration', 'Alert', 'Deploymentmessage', 'Startofmission', 'Endofmission', 'DeploymentDuration', 'Deployed', 'Rotation', 'Comments']
        #     0          1          2          3          4          5                    6          7          8                       9          10          11          12          13             14            15              16          17          18                    19                    20                21          22          23          24
        
        # if empty name -> Alert, otherwise -> Deployment

#       OBSOLETE:

#        # group records by appeal code
#        acodes = list(set([a[2] for a in records[2:]]))
#        for code in acodes:
#            try:
#                appeal = Appeal.objects.get(code=code)
#            except ObjectDoesNotExist:
#                not_found.append(code)
#                continue
#
#            existing_docs = list(appeal.appealdocument_set.all())
#            docs = [a for a in records if a[2] == code]
#            for doc in docs:
#                exists = len([a for a in existing_docs if a.document_url == doc[0]]) > 0
#                if exists:
#                    existing.append(doc[0])
#                else:
#                    try:
#                        created_at = self.parse_date(doc[5])
#                    except:
#                        created_at = None
#
#                    AppealDocument.objects.create(
#                        document_url=doc[0],
#                        name=doc[4],
#                        created_at=created_at,
#                        appeal=appeal,
#                    )
#                    created.append(doc[0])
        logger.info('%s Deployments created' % len(created))
        logger.info('%s existing Deployments' % len(existing))
        logger.warn('%s documents without appeals in system' % len(not_found))
