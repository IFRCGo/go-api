import requests
from requests.auth import HTTPBasicAuth
import xmltodict
import json

from django.core.management.base import BaseCommand
from django.conf import settings

from api.logger import logger
from api.models import (
    Country,
    CronJob,
    CronJobStatus,
    CountryCapacityStrengthening
)


class Command(BaseCommand):
    help = "Add ns contact details"

    def handle(self, *args, **kwargs):
        logger.info('Starting NS Contacts')

        # OCAC Assessment
        OCAC_DATA_API = f"https://data-api.ifrc.org/api/ocacpublic?apiKey={settings.FDRS_APIKEY}"
        resp_ocac = requests.get(OCAC_DATA_API)
        if resp_ocac.status_code != 200:
            text_to_log = "Error querying OCAC at " + url
            logger.error(text_to_log)
            logger.error(resp_ocac.content)
            body = {
                "name": "ingest_ns_contact",
                "message": text_to_log,
                "status": CronJobStatus.ERRONEOUS,
            }
            CronJob.sync_cron(body)
            raise Exception("Error querying OCAC_DATA_API")

        resp_ocac_data = resp_ocac.json()
        final_output = []
        ocaa_count = 0
        for item in resp_ocac_data:
            ocaa_count += 1
            data = {
                'assessment_code': item['AssementCode'],
                'year': item['YearOfAssesment'],
                'submission_date': item['SubmissionDate'],
                'url': item['URL'],
                'country': Country.objects.filter(fdrs=item['NsId']).first(),
                'assessment_type': CountryCapacityStrengthening.AssessmentType.OCAC
            }
            CountryCapacityStrengthening.objects.create(**data)

        text_to_log = "%s Ns capacity added" % ocaa_count
        logger.info(text_to_log)
        body = {
            "name": "ingest_ns_capaciity",
            "message": text_to_log,
            "num_result": ocaa_count,
            "status": CronJobStatus.SUCCESSFUL
        }
        CronJob.sync_cron(body)

        # BOCA Assessment
        BOCA_DATA_API = f"https://data-api.ifrc.org/api/bocapublic?apiKey={settings.FDRS_APIKEY}"
        resp_boca = requests.get(BOCA_DATA_API)
        resp_boca_data = resp_boca.json()
        for item in resp_boca_data:
            country = Country.objects.filter(fdrs=item['NsId']).first()
            if country and 'BranchName' in item:
                data = {
                    'assessment_code': item['AssementCode'],
                    'year': item['YearOfAssesment'],
                    'submission_date': item['SubmissionDate'],
                    'url': item['URL'],
                    'country': Country.objects.filter(fdrs=item['NsId']).first(),
                    'assessment_type': CountryCapacityStrengthening.AssessmentType.BOCA,
                    'branch_name': item['BranchName']
                }
                CountryCapacityStrengthening.objects.create(**data)
