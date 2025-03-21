from datetime import datetime, timezone

import requests
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from sentry_sdk.crons import monitor

from api.logger import logger
from api.models import (
    Appeal,
    AppealDocument,
    AppealDocumentType,
    CronJob,
    CronJobStatus,
)
from main.sentry import SentryMonitor

CRON_NAME = "sync_appealdocs"
PUBLIC_SOURCE = "https://go-api.ifrc.org/api/publicsiteappeals?Hidden=false&BaseAppealnumber="
FEDNET_SOURCE = "https://go-api.ifrc.org/Api/FedNetAppeals?Hidden=false&BaseAppealnumber="
# Recently not needed, due to all docs are in the above ^ ones:
# DONOR_SOURCE = "https://go-api.ifrc.org/api/PublicSiteDonorResponses?AppealCode="


class Command(BaseCommand):
    help = "Ingest existing appeal documents"

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            "--fullscan",
            action="store_true",
            help="Run a full scan on all appeals",
        )

    def parse_date(self, date_string):
        timeformat = "%Y-%m-%dT%H:%M:%S"
        return datetime.strptime(date_string[:18], timeformat).replace(tzinfo=timezone.utc)

    @monitor(monitor_slug=SentryMonitor.SYNC_APPEALDOCS)
    def handle(self, *args, **options):
        logger.info("Starting appeal document ingest")

        if options["fullscan"]:
            # TODO: should be inserted to cron jobs, 4 monthly or so. Or create a calendar note for maintainer.
            # If the `--fullscan` option is passed (at the end of command), check ALL appeals. Runs 20 mins!
            print("Doing a full scan of all Appeals")
            qset = Appeal.objects.all()
        else:
            # By default, only check appeals for the past 3 months where Appeal Documents is 0
            now = datetime.now().replace(tzinfo=timezone.utc)
            six_months_ago = now - relativedelta(months=6)
            # This was the original qset, but it wouldn't get newer docs for the same Appeals
            # qset = Appeal.objects.filter(appealdocument__isnull=True).filter(end_date__gt=six_months_ago)
            qset = Appeal.objects.filter(end_date__gt=six_months_ago)

        # qset = Appeal.objects.filter(code='Something')  # could help debug
        # First get all Appeal Codes
        appeal_codes = [a.code for a in qset]
        auth = (settings.APPEALS_USER, settings.APPEALS_PASS)
        headers = {"Accept": "application/json"}
        existing = []
        created = []

        # Documents for each appeal code
        for code in appeal_codes:
            code = code.replace(" ", "")
            listone = requests.get(PUBLIC_SOURCE + str(code), auth=auth, headers=headers).json()
            listtwo = requests.get(FEDNET_SOURCE + str(code), auth=auth, headers=headers).json()
            # list3 = requests.get(DONOR_SOURCE + str(code), auth=auth, headers=headers).json()
            results = listone + listtwo  # do not tempt list(set(...)), because: unhashable type: 'dict'
            for result in results:
                appeals = Appeal.objects.filter(code=code).values_list("id", flat=True)
                appeal_id = appeals[0]
                # Should be always True due to we started from appeals:
                if appeal_id:
                    # Filter BaseDirectory + BaseFileName == document_url and via code, like 'MGR00001':
                    pre = "https://www.ifrc.org" if result["BaseDirectory"][:21] == "/docs/appeals/Active/" else ""
                    document_url = pre + result["BaseDirectory"] + result["BaseFileName"].replace(" ", "-")
                    # Andras Lazar suggested to use dashes instead the spaces in the appealdoc filenames – 2025.02.28
                    already_exists = AppealDocument.objects.filter(document_url=document_url).filter(appeal_id=appeal_id)
                    if already_exists:
                        existing.append(document_url)
                    else:
                        try:
                            iso = result["LocationCountryCode"]
                            if not iso:
                                iso = Appeal.objects.get(pk=appeal_id).country.iso
                                if not iso:
                                    logger.warning("Wrong AppealDocument data – unknown country.")
                                    continue
                            appealtype_id = result["AppealsTypeId"]
                            if not appealtype_id or not AppealDocumentType.objects.filter(id=appealtype_id):  # not pk=...!
                                logger.warning("Wrong AppealDocument data – unknown type_id: %s", appealtype_id)
                                continue
                            created_at = None
                            if "AppealsDate" in result:
                                created_at = self.parse_date(result["AppealsDate"])
                            elif "Inserted" in result:
                                created_at = self.parse_date(result["Inserted"])
                            AppealDocument.objects.create(
                                document_url=document_url,
                                appeal_id=appeal_id,
                                name=result["AppealsName"][:100],
                                description=result["AppealOrigType"],
                                type_id=appealtype_id,
                                iso_id=iso,
                                created_at=created_at,
                            )
                            created.append(document_url)
                        except Exception:
                            logger.error("Could not create AppealDocument", exc_info=True)

        logger.info("%s appeal documents created" % len(created))
        logger.info("%s existing appeal documents" % len(existing))

        body = {
            "name": CRON_NAME,
            "message": (
                f"Done ingesting appeals_docs,"
                f" {len(created)} appeal document(s) were created,"
                f" {len(existing)} already exist."
            ),
            "num_result": len(created),
            "status": CronJobStatus.SUCCESSFUL,
        }
        CronJob.sync_cron(body)
