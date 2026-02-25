import json

from django.conf import settings
from django.core.management.base import BaseCommand

from api.logger import logger
from api.molnix_utils import MolnixApi

DEBUG_LEVEL = 2  # Set to 0 for no debug, higher numbers for more verbose debug output


def extract_appraisals(payload):
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    if "original" in payload and isinstance(payload["original"], dict):
        original = payload["original"]
        if "data" in original and isinstance(original["data"], list):
            return original["data"]
    if "appraisals" in payload:
        appraisals = payload["appraisals"]
        if isinstance(appraisals, dict) and "data" in appraisals:
            return appraisals["data"]
        if isinstance(appraisals, list):
            return appraisals
    if "data" in payload and isinstance(payload["data"], list):
        return payload["data"]
    return []


def should_continue(payload, appraisals):
    if not appraisals:
        return False
    if not isinstance(payload, dict):
        return True
    original = payload.get("original")
    if isinstance(original, dict):
        if original.get("next_page_url") in ("", None, False):
            return False
        current_page = original.get("current_page")
        last_page = original.get("last_page")
        if isinstance(current_page, int) and isinstance(last_page, int) and current_page >= last_page:
            return False
    if "next" in payload and not payload["next"]:
        return False
    return True


def log_debug(level, message):
    if DEBUG_LEVEL >= level:
        logger.info("[debug-%d] %s" % (level, message))


class Command(BaseCommand):
    help = "Fetch and print Molnix appraisals"

    def handle(self, *args, **options):
        logger.info("Starting Sync Molnix Appraisals job")
        molnix = MolnixApi(url=settings.MOLNIX_API_BASE, username=settings.MOLNIX_USERNAME, password=settings.MOLNIX_PASSWORD)
        try:
            molnix.login()
            logger.info("Logged into Molnix")
        except Exception as ex:
            logger.error("Failed to login to Molnix API: %s" % str(ex))
            return

        page = 1
        total = 0
        while True:
            log_debug(1, "Fetching page %d" % page)
            data = molnix.call_api(path="appraisals", params={"page": page})
            appraisals = extract_appraisals(data)
            if isinstance(data, dict):
                original = data.get("original") if isinstance(data.get("original"), dict) else {}
                log_debug(
                    1,
                    "Pagination current=%s last=%s next_url=%s count=%d"
                    % (
                        original.get("current_page"),
                        original.get("last_page"),
                        original.get("next_page_url"),
                        len(appraisals),
                    ),
                )
                log_debug(2, "Top-level keys: %s" % sorted(list(data.keys())))
                if original:
                    log_debug(2, "Original keys: %s" % sorted(list(original.keys())))
            if not appraisals:
                log_debug(1, "No appraisals returned, stopping")
                break
            for appraisal in appraisals:
                self.stdout.write(json.dumps(appraisal, indent=2, sort_keys=True))
                total += 1
            if not should_continue(data, appraisals):
                log_debug(1, "Pagination indicates no more pages")
                break
            page += 1

        logger.info("Printed %d appraisals" % total)
        molnix.logout()
