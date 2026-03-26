import json

from django.conf import settings
from django.core.management.base import BaseCommand

from api.logger import logger
from api.molnix_utils import MolnixApi

DEBUG_LEVEL = 2  # Set to 0 for no debug, higher numbers for more verbose debug output
APPRAISALS_PER_PAGE = 15


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


def collect_person_ids(appraiser_records, collected):
    if not isinstance(appraiser_records, list):
        return
    for record in appraiser_records:
        if not isinstance(record, dict):
            continue
        person_id = record.get("person_id")
        if person_id is not None:
            collected.append(person_id)


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


def normalize_appraisal(appraisal):
    if not isinstance(appraisal, dict):
        return {}
    cleaned = remove_tags_and_deployments(appraisal, "appraisal")
    return {
        "id": cleaned.get("id"),
        "target_id": cleaned.get("target_id"),
        "stage": cleaned.get("stage"),
        "created_at": cleaned.get("created_at"),
        "updated_at": cleaned.get("updated_at"),
        "appraisers_count": cleaned.get("appraisers_count"),
        "objectives": cleaned.get("objectives"),
        "competencies": cleaned.get("competencies"),
        "score": cleaned.get("score"),
        "appraisers": cleaned.get("appraisers"),
    }


def normalize_appraiser(appraiser):
    if not isinstance(appraiser, dict):
        return {}
    cleaned = remove_tags_and_deployments(appraiser)
    return {
        "id": cleaned.get("id"),
        "appraisal_id": cleaned.get("appraisal_id"),
        "appraiser_type": cleaned.get("appraiser_type"),
        "person_id": cleaned.get("person_id"),
        "name": cleaned.get("name"),
        "email": cleaned.get("email"),
        "position_title": cleaned.get("position_title"),
        "required": cleaned.get("required"),
        "notified_at": cleaned.get("notified_at"),
        "notification_counter": cleaned.get("notification_counter"),
        "completed_at": cleaned.get("completed_at"),
        "created_at": cleaned.get("created_at"),
        "updated_at": cleaned.get("updated_at"),
        "responses": cleaned.get("responses"),
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
        appraisals_stream_count = 0
        appraisers_stream_count = 0
        while True:
            log_debug(1, "Fetching page %d" % page)
            data = molnix.call_api(path="appraisals", params={"page": page, "per_page": APPRAISALS_PER_PAGE})
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
                if not isinstance(appraisal, dict):
                    continue
                appraisal_data = normalize_appraisal(appraisal.get("appraisal"))
                if appraisal_data:
                    self.stdout.write(
                        json.dumps({"record_type": "molnix_appraisal", "data": appraisal_data}, indent=2, sort_keys=True)
                    )
                    appraisals_stream_count += 1
                appraiser_data = normalize_appraiser(appraisal)
                if appraiser_data:
                    self.stdout.write(
                        json.dumps({"record_type": "molnix_appraiser", "data": appraiser_data}, indent=2, sort_keys=True)
                    )
                    appraisers_stream_count += 1
                collect_person_ids([appraiser_data], person_ids)
                total += 1
            if not should_continue(data, appraisals):
                log_debug(1, "Pagination indicates no more pages")
                break
            page += 1

        unique_person_ids = sorted({pid for pid in person_ids if pid is not None})
        log_debug(1, "Collected %d person_id values" % len(unique_person_ids))
        for person_id in unique_person_ids:
            log_debug(1, "Fetching person_id %s" % person_id)
            person_data = molnix.call_api(path="people/%s" % person_id)
            filtered_person_data = filter_person_data(person_data)
            if not filtered_person_data:
                log_debug(2, "No person payload found for person_id %s" % person_id)
            self.stdout.write(
                json.dumps(
                    {"record_type": "molnix_person_sex", "person_id": person_id, "data": filtered_person_data},
                    indent=2,
                    sort_keys=True,
                )
            )
        # log_debug(1, "Smoke test: response_capacity endpoint")
        # response_capacity_data = molnix.call_api(path="response_capacity")
        # self.stdout.write(json.dumps(response_capacity_data, indent=2, sort_keys=True))
        logger.info("Printed %d items (appraisals=%d appraisers=%d)" % (total, appraisals_stream_count, appraisers_stream_count))
        molnix.logout()
