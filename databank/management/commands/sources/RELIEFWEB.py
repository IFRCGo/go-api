import datetime
import logging

import requests
from django.conf import settings

from databank.models import Month, PastCrisesEvent, PastEpidemic

from .utils import catch_error, get_country_by_iso3

logger = logging.getLogger(__name__)

DISASTER_API = f"https://api.reliefweb.int/v1/disasters?appname={settings.RELIEF_WEB_APP_NAME}"
RELIEFWEB_DATETIME_FORMAT = "%Y-%m-%d"


def parse_date(date):
    # Only works for reliefweb dates
    # For python >= 3.7 RELIEFWEB_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
    return datetime.datetime.strptime(date.split("T")[0], RELIEFWEB_DATETIME_FORMAT)


def _post_reliefweb(query_params, url, context, *, allow_fallback=True):
    try:
        response = requests.post(url, json=query_params)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response else None
        if status_code == 410:
            fallback_url = url.replace("/disasters/?", "/disasters?")
            if allow_fallback and fallback_url != url:
                logger.warning(
                    "ReliefWeb API returned 410 Gone for %s. Retrying with fallback URL: %s",
                    context,
                    fallback_url,
                )
                return _post_reliefweb(query_params, fallback_url, context, allow_fallback=False)
            logger.warning(
                "ReliefWeb API returned 410 Gone for %s. Skipping %s prefetch. URL: %s",
                DISASTER_API,
                context,
                url,
            )
            return None
        raise
    except requests.RequestException:
        logger.exception("ReliefWeb API request failed for %s. URL: %s", context, url)
        raise
    except ValueError:
        logger.exception("ReliefWeb API returned invalid JSON for %s. URL: %s", context, url)
        raise


def _crises_event_prefetch():
    query_params = {
        "limit": 1000,
        "filter": {
            "operator": "AND",
            "conditions": [
                {
                    "field": "primary_type.code",
                    "value": [type_code for type_code, _ in PastCrisesEvent.CHOICES],
                    "operator": "OR",
                }
            ],
        },
        "fields": {"include": ["date.created", "primary_country.iso3", "primary_type.code"]},
    }

    url = DISASTER_API
    data = {}
    while True:
        response = _post_reliefweb(query_params, url, "crises_event")
        if response is None:
            return {}

        for disaster in response["data"]:
            disaster = disaster["fields"]
            iso3 = disaster["primary_country"]["iso3"].upper()
            pcountry = get_country_by_iso3(iso3)
            if pcountry is None:
                continue
            iso2 = pcountry.alpha_2
            dt = parse_date(disaster["date"]["created"])
            disaster_data = {
                "event": disaster["primary_type"]["code"],
                "year": dt.year,
                "month": dt.month,
            }
            if data.get(iso2) is None:
                data[iso2] = [disaster_data]
            else:
                data[iso2].append(disaster_data)

        if "next" not in response["links"]:
            break
        url = response["links"]["next"]["href"]
    return data


def _epidemics_prefetch():
    query_params = {
        "limit": 1000,
        "filter": {
            "operator": "AND",
            "conditions": [
                {
                    "field": "primary_type.code",
                    "value": ["EP"],
                },
            ],
        },
        "fields": {"include": ["name", "date.created", "primary_country.iso3"]},
    }

    url = DISASTER_API
    data = {}
    while True:
        response = _post_reliefweb(query_params, url, "epidemics")
        if response is None:
            return {}

        for epidemic in response["data"]:
            epidemic = epidemic["fields"]
            iso3 = epidemic["primary_country"]["iso3"].upper()
            pcountry = get_country_by_iso3(iso3)
            if pcountry is None:
                continue
            iso2 = pcountry.alpha_2
            dt = parse_date(epidemic["date"]["created"])
            name = epidemic["name"]
            selected_epidemic_type = None

            # Simple Text Search
            for epidemic_type, _ in PastEpidemic.CHOICES:
                if epidemic_type.lower() in name.lower():
                    selected_epidemic_type = epidemic_type
            if selected_epidemic_type is None:
                continue

            epidemic_data = {
                "epidemic": selected_epidemic_type,
                "year": dt.year,
                "month": dt.month,
            }

            if data.get(iso2) is None:
                data[iso2] = [epidemic_data]
            else:
                data[iso2].append(epidemic_data)

        if "next" not in response["links"]:
            break
        url = response["links"]["next"]
    return data


@catch_error()
def prefetch():
    crises_event = _crises_event_prefetch()
    epidemics = _epidemics_prefetch()

    return (
        {
            "crises_event": crises_event,
            "epidemics": epidemics,
        },
        len(crises_event) + len(epidemics),
        DISASTER_API,
    )


@catch_error()
def load(country, overview, relief_data):
    if not country.iso or relief_data is None:
        return

    iso2 = country.iso.upper()

    overview.past_crises_events = [
        {
            "id": index + 1,
            "event": data["event"],
            "year": data["year"],
            "month": data["month"],
            "month_display": str(Month.LABEL_MAP.get(data["month"])),
            "event_display": str(PastCrisesEvent.LABEL_MAP.get(data["event"])),
        }
        for index, data in enumerate(relief_data["crises_event"].get(iso2) or [])
    ]

    overview.past_epidemics = [
        {
            "id": index + 1,
            "epidemic": data["epidemic"],
            "year": data["year"],
            "month": data["month"],
            "month_display": str(Month.LABEL_MAP.get(data["month"])),
            "event_display": str(PastEpidemic.LABEL_MAP.get(data["epidemic"])),
        }
        for index, data in enumerate(relief_data["epidemics"].get(iso2) or [])
    ]
    overview.save()
