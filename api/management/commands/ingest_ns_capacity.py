import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from sentry_sdk.crons import monitor

from api.logger import logger
from api.models import Country, CountryCapacityStrengthening, CronJob, CronJobStatus
from main.sentry import SentryMonitor


class Command(BaseCommand):
    help = "Add ns contact details"

    @monitor(monitor_slug=SentryMonitor.INGEST_NS_CAPACITY)
    @transaction.atomic
    def handle(self, *args, **kwargs):
        logger.info("Starting NS Contacts")

        # OCAC Assessment
        OCAC_DATA_API = f"https://data-api.ifrc.org/api/ocacpublic?apiKey={settings.FDRS_APIKEY}"
        resp_ocac = requests.get(OCAC_DATA_API)
        if resp_ocac.status_code != 200:
            text_to_log = "Error querying OCAC at " + OCAC_DATA_API
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
        ocaa_count = 0
        country_capacity_ids = []
        for item in resp_ocac_data:
            ocaa_count += 1
            data = {
                "assessment_code": item["AssementCode"],
                "year": item["YearOfAssesment"],
                "submission_date": item["SubmissionDate"],
                "url": item["URL"],
                "country": Country.objects.filter(fdrs=item["NsId"]).first(),
                "assessment_type": CountryCapacityStrengthening.AssessmentType.OCAC,
            }
            country_capacity_ocac, created = CountryCapacityStrengthening.objects.get_or_create(
                country=data["country"],
                assessment_code=data["assessment_code"],
                assessment_type=data["assessment_type"],
                defaults={
                    "submission_date": data["submission_date"],
                    "url": data["url"],
                    "year": data["year"],
                },
            )
            if not created:
                country_capacity_ocac.submission_date = data["submission_date"]
                country_capacity_ocac.url = data["url"]
                country_capacity_ocac.year = data["year"]
                country_capacity_ocac.save(update_fields=["submission_date", "url", "year"])
            country_capacity_ids.append(country_capacity_ocac.pk)

        text_to_log = "%s Ns capacity added" % ocaa_count
        logger.info(text_to_log)
        body = {
            "name": "ingest_ns_capacity",
            "message": text_to_log,
            "num_result": ocaa_count,
            "status": CronJobStatus.SUCCESSFUL,
        }
        CronJob.sync_cron(body)

        # BOCA Assessment
        BOCA_DATA_API = f"https://data-api.ifrc.org/api/bocapublic?apiKey={settings.FDRS_APIKEY}"
        resp_boca = requests.get(BOCA_DATA_API)
        resp_boca_data = resp_boca.json()
        for item in resp_boca_data:
            country = Country.objects.filter(fdrs=item["NsId"]).first()
            if country and "BranchName" in item:
                data = {
                    "assessment_code": item["AssementCode"],
                    "year": item["YearOfAssesment"],
                    "submission_date": item["SubmissionDate"],
                    "url": item["URL"],
                    "country": Country.objects.filter(fdrs=item["NsId"]).first(),
                    "assessment_type": CountryCapacityStrengthening.AssessmentType.BOCA,
                    "branch_name": item["BranchName"],
                }
                country_capacity_boca, created = CountryCapacityStrengthening.objects.get_or_create(
                    country=data["country"],
                    assessment_code=data["assessment_code"],
                    assessment_type=data["assessment_type"],
                    defaults={
                        "year": data["year"],
                        "branch_name": data["branch_name"],
                        "submission_date": data["submission_date"],
                        "url": data["url"],
                    },
                )
                if not created:
                    country_capacity_boca.submission_date = data["submission_date"]
                    country_capacity_boca.url = data["url"]
                    country_capacity_boca.year = data["year"]
                    country_capacity_boca.branch_name = data["branch_name"]
                    country_capacity_boca.save(update_fields=["submission_date", "url", "year", "branch_name"])
                country_capacity_ids.append(country_capacity_boca.pk)
        # Delete the country capacity strengthening which are not available in the source
        CountryCapacityStrengthening.objects.exclude(id__in=country_capacity_ids).delete()
