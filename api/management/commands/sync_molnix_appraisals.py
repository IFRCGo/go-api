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


def remove_tags_and_deployments(value, parent_key=None):
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            if key == "tags":
                continue
            if parent_key == "appraisal" and key == "deployment":
                continue
            cleaned[key] = remove_tags_and_deployments(item, key)
        return cleaned
    if isinstance(value, list):
        return [remove_tags_and_deployments(item, parent_key) for item in value]
    return value


def collect_person_ids(value, collected):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "person_id":
                collected.append(item)
            else:
                collect_person_ids(item, collected)
        return
    if isinstance(value, list):
        for item in value:
            collect_person_ids(item, collected)


def find_person_payload(value):
    # if isinstance(value, dict):
    if any(key in value for key in ("sex", "fullname", "organization", "current_availability")):
        return value
    for item in value.values():
        found = find_person_payload(item)
        if found is not None:
            return found
    # occured never:
    # if isinstance(value, list):
    #     for item in value:
    #         found = find_person_payload(item)
    #         if found is not None:
    #             return found
    return None


def filter_person_data(person_data):
    payload = find_person_payload(person_data)
    if not isinstance(payload, dict):
        return {}
    return {
        "sex": payload.get("sex"),
        "fullname": payload.get("fullname"),
        "organization": payload.get("organization"),
        "current_availability": payload.get("current_availability"),
    }


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
        person_ids = []
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
                collect_person_ids(appraisal, person_ids)
                cleaned_appraisal = remove_tags_and_deployments(appraisal)
                self.stdout.write(json.dumps(cleaned_appraisal, indent=2, sort_keys=True))
                total += 1
            if not should_continue(data, appraisals):
                log_debug(1, "Pagination indicates no more pages")
                break
            page += 1

        unique_person_ids = sorted({pid for pid in person_ids if pid is not None})
        # self.stdout.write(json.dumps(unique_person_ids, indent=2, sort_keys=True))
        log_debug(1, "Collected %d person_id values" % len(unique_person_ids))
        for person_id in unique_person_ids:
            log_debug(1, "Fetching person_id %s" % person_id)
            person_data = molnix.call_api(path="people/%s" % person_id)
            filtered_person_data = filter_person_data(person_data)
            if not filtered_person_data:
                log_debug(2, "No person payload found for person_id %s" % person_id)
            self.stdout.write(json.dumps(filtered_person_data, indent=2, sort_keys=True))
        # log_debug(1, "Smoke test: response_capacity endpoint")
        # response_capacity_data = molnix.call_api(path="response_capacity")
        # self.stdout.write(json.dumps(response_capacity_data, indent=2, sort_keys=True))
        logger.info("Printed %d appraisals" % total)
        molnix.logout()
