import datetime
import requests

# from django.conf import settings
# from api.utils import base64_encode

from .utils import catch_error, get_country_by_iso2


FTS_URL = 'https://api.hpc.tools/v1/public/fts/flow?countryISO3={0}&groupby=year&report=3'
EMERGENCY_URL = 'https://api.hpc.tools/v1/public/emergency/country/{0}'

HEADERS = {
    # TODO: USE Crendentils here
    # 'Authorization': 'Basic {}'.format(base64_encode(settings.HPC_CREDENTIAL))
}


@catch_error()
def load(country, overview, _):
    pcountry = get_country_by_iso2(country.iso)
    if pcountry is None:
        return
    fts_data = requests.get(FTS_URL.format(pcountry.alpha_3), headers=HEADERS).json()
    emg_data = requests.get(EMERGENCY_URL.format(pcountry.alpha_3), headers=HEADERS).json()

    c_data = {}

    # fundingTotals, pledgeTotals
    for fund_area in ['fundingTotals', 'pledgeTotals']:
        fund_area_data = fts_data['data']['report3'][fund_area]['objects']
        if len(fund_area_data) > 0:
            for v in fund_area_data[0]['objectsBreakdown']:
                try:
                    year = int(v['name'])
                    totalFunding = v['totalFunding']
                except ValueError:
                    continue
                if year not in c_data:
                    c_data[year] = {fund_area: totalFunding}
                else:
                    c_data[year][fund_area] = totalFunding

    # numActivations
    for v in emg_data['data']:
        try:
            year = datetime.datetime.strptime(
                v['date'].split('T')[0],
                '%Y-%m-%d',
            ).year
        except ValueError:
            continue
        if year not in c_data:
            c_data[year] = {'numActivations': 1}
        else:
            c_data[year]['numActivations'] = c_data[year].get('numActivations', 0) + 1

    overview.fts_data = [
        {
            'year': year,
            **values,
        }
        for year, values in c_data.items()
    ]
    overview.save()
