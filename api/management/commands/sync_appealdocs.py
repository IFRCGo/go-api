import requests
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from api.models import Appeal, AppealDocument, CronJob, CronJobStatus
from api.logger import logger
from collections import defaultdict
from django.conf import settings

CRON_NAME = "sync_appealdocs"
PUBLIC_SOURCE = "https://go-api.ifrc.org/api/publicsiteappeals?Hidden=false&Appealnumber="
FEDNET_SOURCE = "https://go-api.ifrc.org/Api/FedNetAppeals?Hidden=false&Appealnumber="


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

    def handle(self, *args, **options):
        logger.info("Starting appeal document ingest")

        if options["fullscan"]:
            # If the `--fullscan` option is passed (at the end of command), check ALL appeals. Runs an hour!
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
            results = listone + listtwo  # do not tempt list(set(...)), because: unhashable type: 'dict'
            for result in results:
                appeals = Appeal.objects.filter(code=code).values_list("id", flat=True)
                appeal_id = appeals[0]
                # Should be always True due to we started from appeals:
                if appeal_id:
                    # Filter BaseDirectory + BaseFileName == document_url and via code, like 'MGR00001':
                    document_url = result["BaseDirectory"] + result["BaseFileName"]
                    already_exists = AppealDocument.objects.filter(document_url=document_url).filter(appeal_id=appeal_id)
                    if already_exists:
                        existing.append(document_url)
                    else:
                        try:
                            created_at = None
                            if "AppealsDate" in result:
                                created_at = self.parse_date(result["AppealsDate"])
                            elif "Inserted" in result:
                                created_at = self.parse_date(result["Inserted"])
                            AppealDocument.objects.create(
                                document_url=document_url,
                                appeal_id=appeal_id,
                                name=result["AppealsName"],
                                description=result["AppealOrigType"],
                                type_id=result["AppealsTypeId"],
                                iso_id=result["LocationCountryCode"],
                                created_at=created_at
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
