import requests
from datetime import datetime, timezone
from django.conf import settings
from django.core.management.base import BaseCommand
from api.models import AppealDocumentType, AppealDocument, Appeal
from api.logger import logger

CRON_NAME = "ingest_appealdocs"
APPEAL_DOCUMENT_TYPES = AppealDocumentType.objects.all()  # used only for read in appealdocument locations from api. You can check them via go-api.ifrc.org/Api/PublicSiteTypes
PUBLIC_SOURCE = "https://go-api.ifrc.org/api/publicsiteappeals?Hidden=false&AppealsTypeID="
FEDNET_SOURCE = "https://go-api.ifrc.org/Api/FedNetAppeals?Hidden=false&AppealsTypeId="


class Command(BaseCommand):
    help = "Add new entries from Access database file"

    @staticmethod
    def parse_date(date_string):
        timeformat = "%Y-%m-%dT%H:%M:%S"
        return datetime.strptime(date_string[:18], timeformat).replace(tzinfo=timezone.utc)

    def load(self, url: str, is_fednet):
        codes = Appeal.objects.values_list("code", flat=True)
        auth = (settings.APPEALS_USER, settings.APPEALS_PASS)
        for adtype in APPEAL_DOCUMENT_TYPES.filter(public_site_or_fednet=is_fednet):
            results = requests.get(url + str(adtype.id), auth=auth, headers={"Accept": "application/json"}).json()
            for result in results:
                # We should match BaseDirectory + BaseFileName == document_url and BaseAppealNumber == code  # 'MGR00001'
                if result["BaseAppealNumber"] in codes:
                    appeals = Appeal.objects.filter(code=result["BaseAppealNumber"]).values_list("id", flat=True)
                    if appeals:
                        document_url = result["BaseDirectory"] + result["BaseFileName"]
                        appeal_docs = AppealDocument.objects.filter(document_url=document_url).filter(appeal_id=appeals[0])
                        if appeal_docs:
                            appeal_doc = appeal_docs[0]  # maybe some other fuzzy filtering via type?
                            appeal_doc.description = result["AppealOrigType"]
                            appeal_doc.type_id = result["AppealsTypeId"]
                            appeal_doc.iso_id = result["LocationCountryCode"]
                            if self.parse_date(result["AppealsDate"]) < appeal_doc.created_at:
                                appeal_doc.created_at = self.parse_date(result["AppealsDate"])
                            try:
                                appeal_doc.save()
                            except Exception:
                                logger.error("Could not update AppealDocuments", exc_info=True)

    def handle(self, **_):
        # Public
        self.stdout.write("Fetching data for appeal_docs:: PUBLIC")
        self.load(PUBLIC_SOURCE, False)
        # Private
        self.stdout.write("Fetching data for appeal_docs:: FEDNET")
        self.load(FEDNET_SOURCE, True)
