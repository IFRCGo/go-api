import datetime
import requests

# from django.conf import settings
# from api.utils import base64_encode

from .utils import catch_error, get_country_by_iso2
from api.models import CronJob, CronJobStatus


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
    fts_data = requests.get(FTS_URL.format(pcountry.alpha_3), headers=HEADERS)
    emg_data = requests.get(EMERGENCY_URL.format(pcountry.alpha_3), headers=HEADERS)

    if fts_data.status_code != 200:
        body = { "name": "FTS_HPC", "message": "Error querying HPC fts data feed at " + FTS_URL, "status": CronJobStatus.ERRONEOUS } # not every case is catched here, e.g. if the base URL is wrong...
        CronJob.sync_cron(body)
    if emg_data.status_code != 200:
        body = { "name": "FTS_HPC", "message": "Error querying HPC emergency data feed at " + EMERGENCY_URL, "status": CronJobStatus.ERRONEOUS } # not every case is catched here, e.g. if the base URL is wrong...
        CronJob.sync_cron(body)
    fts_data = fts_data.json()
    emg_data = emg_data.json()

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

    body = { "name": "FTS_HPC", "message": "Done querying all HPC data feeds at " + FTS_URL + " and " + EMERGENCY_URL, "status": CronJobStatus.SUCCESSFUL }
    CronJob.sync_cron(body)

