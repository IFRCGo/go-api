import json

from django.conf import settings
from django.core.management.base import BaseCommand

from api.logger import logger
from api.molnix_utils import MolnixApi

DEBUG_LEVEL = 2  # Set to 0 for no debug, higher numbers for more verbose debug output
OUTPUT = 0  # 0=print only, 1=print + DB (TODO), 2=DB only (TODO)
APPRAISALS_PER_PAGE = 15
EVENTS_PER_PAGE = 15


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


def extract_events(payload):
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    if "original" in payload and isinstance(payload["original"], dict):
        original = payload["original"]
        if "data" in original and isinstance(original["data"], list):
            return original["data"]
    if "events" in payload:
        events = payload["events"]
        if isinstance(events, dict) and "data" in events:
            return events["data"]
        if isinstance(events, list):
            return events
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


def output_record(stdout, payload):
    if OUTPUT in (0, 1):
        stdout.write(json.dumps(payload, indent=2, sort_keys=True))


def get_deployment_payload(value):
    if isinstance(value, dict):
        return value
    return {}


def extract_list_payload(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        return payload.get("data")
    return []


def extract_org_list(payload):
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    if "original" in payload and isinstance(payload["original"], dict):
        original = payload["original"]
        if isinstance(original.get("data"), list):
            return original.get("data")
    if isinstance(payload.get("data"), list):
        return payload.get("data")
    if isinstance(payload.get("organizations"), list):
        return payload.get("organizations")
    return []


def normalize_org(value, org_lookup):
    if isinstance(value, dict):
        org_id = value.get("id")
        org_name = value.get("name") or org_lookup.get(org_id)
        return org_id, org_name
    if value is None:
        return None, None
    org_id = value
    org_name = org_lookup.get(org_id)
    return org_id, org_name


def build_org_lookup(molnix):
    try:
        payload = molnix.call_api(path="system/organizations")
    except Exception as ex:
        logger.error("Failed to fetch organizations: %s" % str(ex))
        return {}
    orgs = extract_org_list(payload)
    lookup = {}
    for org in orgs:
        if not isinstance(org, dict):
            continue
        org_id = org.get("id")
        org_name = org.get("name")
        if org_id is not None:
            lookup[org_id] = org_name
    log_debug(1, "Loaded %d organizations" % len(lookup))
    return lookup


def safe_call_api(molnix, path, params=None, label=None):
    try:
        return molnix.call_api(path=path, params=params or {})
    except Exception as ex:
        if label is None:
            label = path
        logger.error("Failed to fetch %s: %s" % (label, str(ex)))
        return None


def fetch_deployment_org_ids(molnix, deployment_id, cache):
    if deployment_id is None:
        return None, None
    if deployment_id in cache:
        return cache[deployment_id]
    payload = safe_call_api(molnix, path="deployments/%s" % deployment_id, label="deployment/%s" % deployment_id)
    if not isinstance(payload, dict):
        cache[deployment_id] = (None, None)
        return cache[deployment_id]
    sending_org = payload.get("sending_organization")
    receiving_org = payload.get("receiving_organization")
    sending_id = sending_org.get("id") if isinstance(sending_org, dict) else sending_org
    receiving_id = receiving_org.get("id") if isinstance(receiving_org, dict) else receiving_org
    cache[deployment_id] = (sending_id, receiving_id)
    return cache[deployment_id]


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
    if not isinstance(value, dict):
        return None
    if any(key in value for key in ("sex", "organization", "current_availability", "outofscope")):
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


def filter_person_data(person_data, org_lookup):
    payload = find_person_payload(person_data)
    if not isinstance(payload, dict):
        return {}
    org_id, org_name = normalize_org(payload.get("organization"), org_lookup)
    return {
        "sex": payload.get("sex"),
        "organization_id": org_id,
        "organization_name": org_name,
        "current_availability": payload.get("current_availability"),
        "outofscope": payload.get("outofscope"),
    }


def normalize_appraisal(appraisal, sending_org_id=None, receiving_org_id=None):
    if not isinstance(appraisal, dict):
        return {}
    deployment = get_deployment_payload(appraisal.get("deployment"))
    return {
        "molnix_id": appraisal.get("id"),
        "target_id": appraisal.get("target_id"),
        "deployment_molnix_id": deployment.get("id"),
        "stage": appraisal.get("stage"),
        "appraisers_count": appraisal.get("appraisers_count"),
        "score": appraisal.get("score"),
        "deployment_country_id": deployment.get("country_id"),
        "deployment_start": deployment.get("start"),
        "deployment_end": deployment.get("end"),
        "deployment_title": deployment.get("title"),
        "sending_organization_id": sending_org_id,
        "receiving_organization_id": receiving_org_id,
        "deployment_tags_json": deployment.get("tags"),
        "competencies_json": appraisal.get("competencies"),
        "created_at": appraisal.get("created_at"),
        "updated_at": appraisal.get("updated_at"),
    }


def normalize_appraiser(appraiser):
    if not isinstance(appraiser, dict):
        return {}
    return {
        "molnix_id": appraiser.get("id"),
        "appraisal_molnix_id": appraiser.get("appraisal_id"),
        "appraiser_type": appraiser.get("appraiser_type"),
        "person_id": appraiser.get("person_id"),
        "required": appraiser.get("required"),
        "notified_at": appraiser.get("notified_at"),
        "completed_at": appraiser.get("completed_at"),
        "created_at": appraiser.get("created_at"),
        "updated_at": appraiser.get("updated_at"),
    }


def normalize_event_participation(event, org_lookup):
    if not isinstance(event, dict):
        return []
    org_id, org_name = normalize_org(event.get("organization"), org_lookup)
    people = event.get("person") if isinstance(event.get("person"), list) else []
    records = []
    for person in people:
        if not isinstance(person, dict):
            continue
        pivot = person.get("pivot") if isinstance(person.get("pivot"), dict) else {}
        record = {
            "event_id": event.get("id"),
            "event_name": event.get("name"),
            "person_id": person.get("id"),
            "event_person_role": pivot.get("role"),
            "event_type": event.get("event_type"),
            "event_scale_type": event.get("type"),
            "event_from": event.get("from"),
            "event_to": event.get("to"),
            "participant_start": pivot.get("start"),
            "participant_end": pivot.get("end"),
            "requested": pivot.get("requested"),
            "event_organization_id": org_id,
            "event_organization_name": org_name,
            "venue": event.get("venue"),
            "tags_json": event.get("tags"),
        }
        records.append(record)
    return records


def handle_person_ids(molnix, person_ids, org_lookup, stdout):
    person_snapshot_cache = {}
    for person_id in person_ids:
        cached_snapshot = person_snapshot_cache.get(person_id)
        if cached_snapshot is not None:
            output_record(stdout, {"record_type": "rrms_person_snapshot", "data": cached_snapshot})
            continue
        log_debug(1, "Fetching person_id %s" % person_id)
        person_data = safe_call_api(molnix, path="people/%s" % person_id, label="people/%s" % person_id)
        if person_data is None:
            log_debug(2, "Skipping person_id %s due to people endpoint failure" % person_id)
            continue
        roles_payload = safe_call_api(molnix, path="people/%s/roles" % person_id, label="people/%s/roles" % person_id)
        languages_payload = safe_call_api(molnix, path="people/%s/languages" % person_id, label="people/%s/languages" % person_id)
        tags_payload = safe_call_api(molnix, path="people/%s/tags" % person_id, label="people/%s/tags" % person_id)
        filtered_person_data = filter_person_data(person_data, org_lookup)
        if not filtered_person_data:
            log_debug(2, "No person payload found for person_id %s" % person_id)
            filtered_person_data = {}
        filtered_person_data.update(
            {
                "person_id": person_id,
                "roles_json": extract_list_payload(roles_payload) if roles_payload is not None else [],
                "languages_json": extract_list_payload(languages_payload) if languages_payload is not None else [],
                "tags_json": extract_list_payload(tags_payload) if tags_payload is not None else [],
            }
        )
        person_snapshot_cache[person_id] = filtered_person_data
        output_record(stdout, {"record_type": "rrms_person_snapshot", "data": filtered_person_data})


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

        org_lookup = build_org_lookup(molnix)

        if OUTPUT == 2:
            self.stdout.write("OUTPUT=2 (DB-only mode) is selected; DB writes are not implemented yet.")

        page = 1
        total = 0
        person_ids = []
        event_person_ids = []
        appraisals_stream_count = 0
        appraisers_stream_count = 0
        events_stream_count = 0
        deployment_org_cache = {}
        while True:
            log_debug(1, "Fetching page %d" % page)
            data = safe_call_api(
                molnix, path="appraisals", params={"page": page, "per_page": APPRAISALS_PER_PAGE}, label="appraisals"
            )
            if data is None:
                log_debug(1, "Appraisals call failed, stopping")
                break
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
                appraisal_payload = appraisal.get("appraisal")
                deployment_id = appraisal_payload.get("deployment", {}).get("id") if isinstance(appraisal_payload, dict) else None
                sending_org_id, receiving_org_id = fetch_deployment_org_ids(molnix, deployment_id, deployment_org_cache)
                appraisal_data = normalize_appraisal(appraisal_payload, sending_org_id, receiving_org_id)
                if appraisal_data:
                    output_record(self.stdout, {"record_type": "molnix_appraisal", "data": appraisal_data})
                    appraisals_stream_count += 1
                appraiser_data = normalize_appraiser(appraisal)
                if appraiser_data:
                    output_record(self.stdout, {"record_type": "molnix_appraiser", "data": appraiser_data})
                    appraisers_stream_count += 1
                collect_person_ids([appraiser_data], person_ids)
                total += 1
            if not should_continue(data, appraisals):
                log_debug(1, "Pagination indicates no more pages")
                break
            page += 1

        event_page = 1
        while True:
            log_debug(1, "Fetching events page %d" % event_page)
            events_payload = safe_call_api(
                molnix, path="events", params={"page": event_page, "per_page": EVENTS_PER_PAGE}, label="events"
            )
            if events_payload is None:
                log_debug(1, "Events call failed, stopping")
                break
            events = extract_events(events_payload)
            if isinstance(events_payload, dict):
                original = events_payload.get("original") if isinstance(events_payload.get("original"), dict) else {}
                log_debug(
                    1,
                    "Events pagination current=%s last=%s next_url=%s count=%d"
                    % (
                        original.get("current_page"),
                        original.get("last_page"),
                        original.get("next_page_url"),
                        len(events),
                    ),
                )
            if not events:
                log_debug(1, "No events returned, stopping")
                break
            for event in events:
                records = normalize_event_participation(event, org_lookup)
                for record in records:
                    output_record(self.stdout, {"record_type": "rrms_event_participation", "data": record})
                    events_stream_count += 1
                    if record.get("person_id") is not None:
                        event_person_ids.append(record.get("person_id"))
            if not should_continue(events_payload, events):
                log_debug(1, "Events pagination indicates no more pages")
                break
            event_page += 1

        appraisal_person_ids = sorted({pid for pid in person_ids if pid is not None})
        event_person_ids = sorted({pid for pid in event_person_ids if pid is not None})
        unique_person_ids = sorted({pid for pid in appraisal_person_ids + event_person_ids if pid is not None})
        log_debug(
            1,
            "Collected %d appraisal person_id values and %d event person_id values"
            % (len(appraisal_person_ids), len(event_person_ids)),
        )
        handle_person_ids(molnix, appraisal_person_ids, org_lookup, self.stdout)
        handle_person_ids(molnix, event_person_ids, org_lookup, self.stdout)
        # log_debug(1, "Smoke test: response_capacity endpoint")
        # response_capacity_data = molnix.call_api(path="response_capacity")
        # self.stdout.write(json.dumps(response_capacity_data, indent=2, sort_keys=True))
        if OUTPUT in (0, 1):
            logger.info(
                "Printed %d items (appraisals=%d appraisers=%d events=%d persons=%d)"
                % (
                    total,
                    appraisals_stream_count,
                    appraisers_stream_count,
                    events_stream_count,
                    len(unique_person_ids),
                )
            )
        if OUTPUT == 2:
            self.stdout.write("Completed DB-only run (writes not implemented yet).")
        molnix.logout()
