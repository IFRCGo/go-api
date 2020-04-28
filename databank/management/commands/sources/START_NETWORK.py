import re
import datetime
import requests
import csv

from .utils import catch_error, get_country_by_name


API_ENDPOINT = 'https://startnetwork.org/api/v1/start-fund-all-alerts'
DATE_FORMATS = (
    '%d %b %Y - %H:%S',
    '%m/%d/%Y %H:%M'
)


def parse_amount(amount_in_string):
    c_string = re.sub('[^0-9]', '', amount_in_string).strip()
    if c_string:
        return int(c_string)


def parse_alert_date(date):
    for date_format in DATE_FORMATS:
        try:
            return datetime.datetime.strptime(date, date_format)
        except ValueError:  # Try again with another format
            pass


@catch_error()
def prefetch():
    data = {}
    rs = requests.get(API_ENDPOINT)
    rs.raise_for_status()
    rs = rs.text.splitlines()

    CronJobSum = 0
    for row in csv.DictReader(rs):
        # Some value are like `Congo [DRC]`
        country = get_country_by_name(row['Country'].split('[')[0].strip())
        date = parse_alert_date(row['Alert date'])
        if country is None or date is None:
            continue
        iso2 = country.alpha_2
        alert_data = {
            'date': date.isoformat(),
            'alert': row['Alert'],
            'alert_type': row['Alert type'],
            'amount_awarded': parse_amount(row['Amount Awarded']),
            'crisis_type': row['Crisis Type'],
        }

        if data.get(iso2) is None:
            data[iso2] = [alert_data]
        else:
            data[iso2].append(alert_data)
        CronJobSum += 1
    return data, CronJobSum, API_ENDPOINT


@catch_error()
def load(country, overview, data):
    if country.iso is None or data is None or data.get(country.iso.upper()) is None:
        return

    overview.start_network_data = data[country.iso.upper()]
    overview.save()
