import requests
import datetime
import logging

from api.models import District

from .utils import catch_error, get_country_by_iso3


logger = logging.getLogger(__name__)
API_ENDPOINT = 'https://api.worldbank.org/v2/country/ALL/indicator/SP.POP.TOTL'


@catch_error()
def prefetch():
    data = {}

    url = API_ENDPOINT
    page = 1
    now = datetime.datetime.now()
    daterange = f'{now.year - 10}:{now.year}'
    while True:
        # TODO: lastupdated
        rs = requests.get(f'{url}?date={daterange}', params={
            'format': 'json',
            'source': 50,
            'per_page': 5000 - 1,  # WD throws error on 5000
            'page': page,
        }).json()

        for pop_data in rs[1]:
            geo_code = pop_data['country']['id']
            pop = pop_data['value']
            year = pop_data['date']
            if len(geo_code) == 3:   # Admin Level 0
                pcountry = get_country_by_iso3(geo_code)
                if pcountry is None:
                    continue
                geo_id = pcountry.alpha_2
            else:  # Should be Admin Level 1
                # NOTE: District code's structure is <ISO2>_<Number>, so using ISO2
                geo_code = geo_code[-6:]
                pcountry = get_country_by_iso3(geo_code[:3])
                if pcountry is None:
                    continue
                iso2 = pcountry.alpha_2
                geo_id = f'{iso2}{geo_code[3:]}'

            geo_id = geo_id.upper()
            if data.get(geo_id) is None or data.get(geo_id)[1] < year:
                data[geo_id] = (pop, year)

        if page >= rs[0]['pages']:
            break
        page += 1
    return data


@catch_error()
def global_load(wd_data):
    if wd_data is None:
        return

    for district in District.objects.all():
        if not district.code:
            continue
        pop, year = wd_data.get(district.code.upper()) or (None, None)
        if pop is None:
            continue
        district.wb_population = pop
        district.wb_year = year
        district.save(update_fields=['wb_population', 'wb_year'])


@catch_error()
def load(country, overview, wd_data):
    if not country.iso or wd_data is None:
        return

    pop, year = wd_data.get(country.iso.upper()) or (None, None)
    if pop is None:
        return
    country.wb_population = pop
    country.wb_year = year
    country.save(update_fields=['wb_population', 'wb_year'])
