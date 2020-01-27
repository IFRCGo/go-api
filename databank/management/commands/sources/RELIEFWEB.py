import logging
import datetime
import json
import requests

from databank.models import PastCrisesEvent, PastEpidemic, Month
from api.models import CronJob, CronJobStatus
from .utils import catch_error, get_country_by_iso3

logger = logging.getLogger(__name__)

DISASTER_API = 'https://api.reliefweb.int/v1/disasters/'
RELIEFWEB_DATETIME_FORMAT = '%Y-%m-%d'


def parse_date(date):
    # Only works for reliefweb dates
    # For python >= 3.7 RELIEFWEB_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
    return datetime.datetime.strptime(date.split('T')[0], RELIEFWEB_DATETIME_FORMAT)


def _crises_event_prefetch():
    query_params = json.dumps({
        'limit': 1000,
        'filter': {
            'operator': 'AND',
            'conditions': [
                {
                    'field': 'primary_type.code',
                    'value': [type_code for type_code, _ in PastCrisesEvent.CHOICES],
                    'operator': 'OR'
                }
            ]
        },
        'fields': {
            'include': ['date.created', 'primary_country.iso3', 'primary_type.code']
        }
    })

    url = DISASTER_API
    data = {}
    while True:
        response = requests.post(url, data=query_params)
        if response.status_code != 200:
            body = { "name": "RELIEFWEB", "message": "Error querying ReliefWeb crisis event feed at " + url, "status": CronJobStatus.ERRONEOUS } # not every case is catched here, e.g. if the base URL is wrong...
            CronJob.sync_cron(body)
        response = response.json()
        for disaster in response['data']:
            disaster = disaster['fields']
            iso3 = disaster['primary_country']['iso3'].upper()
            pcountry = get_country_by_iso3(iso3)
            if pcountry is None:
                continue
            iso2 = pcountry.alpha_2
            dt = parse_date(disaster['date']['created'])
            disaster_data = {
                'event': disaster['primary_type']['code'],
                'year': dt.year,
                'month': dt.month,
            }
            if data.get(iso2) is None:
                data[iso2] = [disaster_data]
            else:
                data[iso2].append(disaster_data)

        if 'next' not in response['links']:
            break
        url = response['links']['next']['href']
    return data


def _epidemics_prefetch():
    query_params = json.dumps({
        'limit': 1000,
        'filter': {
            'operator': 'AND',
            'conditions': [
                {
                    'field': 'primary_type.code',
                    'value': ['EP'],
                },
            ]
        },
        'fields': {
            'include': ['name', 'date.created', 'primary_country.iso3']
        }
    })

    url = DISASTER_API
    data = {}
    while True:
        response = requests.post(url, data=query_params).json()
        if response.status_code != 200:
            body = { "name": "RELIEFWEB", "message": "Error querying ReliefWeb epicemics feed at " + url, "status": CronJobStatus.ERRONEOUS } # not every case is catched here, e.g. if the base URL is wrong...
            CronJob.sync_cron(body)
        for epidemic in response['data']:
            epidemic = epidemic['fields']
            iso3 = epidemic['primary_country']['iso3'].upper()
            pcountry = get_country_by_iso3(iso3)
            if pcountry is None:
                continue
            iso2 = pcountry.alpha_2
            dt = parse_date(epidemic['date']['created'])
            name = epidemic['name']
            selected_epidemic_type = None

            # Simple Text Search
            for epidemic_type, _ in PastEpidemic.CHOICES:
                if epidemic_type.lower() in name.lower():
                    selected_epidemic_type = epidemic_type
            if selected_epidemic_type is None:
                continue

            epidemic_data = {
                'epidemic': selected_epidemic_type,
                'year': dt.year,
                'month': dt.month,
            }

            if data.get(iso2) is None:
                data[iso2] = [epidemic_data]
            else:
                data[iso2].append(epidemic_data)

        if 'next' not in response['links']:
            break
        url = response['links']['next']
    body = { "name": "RELIEFWEB", "message": "Done querying all ReliefWeb feeds at " + url, "status": CronJobStatus.SUCCESSFUL }
    CronJob.sync_cron(body)
    return data


@catch_error()
def prefetch():
    return {
        'crises_event': _crises_event_prefetch(),
        'epidemics': _epidemics_prefetch(),
    }


@catch_error()
def load(country, overview, relief_data):
    if not country.iso or relief_data is None:
        return

    iso2 = country.iso.upper()

    overview.past_crises_events = [
        {
            'id': index + 1,
            'event': data['event'],
            'year': data['year'],
            'month': data['month'],

            'month_display': Month.LABEL_MAP.get(data['month']),
            'event_display': PastCrisesEvent.LABEL_MAP.get(data['event']),
        } for index, data in enumerate(relief_data['crises_event'].get(iso2) or [])
    ]

    overview.past_epidemics = [
        {
            'id': index + 1,
            'epidemic': data['epidemic'],
            'year': data['year'],
            'month': data['month'],

            'month_display': Month.LABEL_MAP.get(data['month']),
            'event_display': PastEpidemic.LABEL_MAP.get(data['epidemic']),
        } for index, data in enumerate(relief_data['epidemics'].get(iso2) or [])
    ]
    overview.save()
