import requests

from databank.models import InformIndicator

from .utils import catch_error, get_country_by_iso3


INFORM_API_ENDPOINT = (
    'https://drmkc.jrc.ec.europa.eu/inform-index/API/InformAPI/Countries/Scores/?Workflowid=261&indicatorId={}'.format(
        ','.join([indicator for indicator, _ in InformIndicator.CHOICES])
    )
)


@catch_error()
def prefetch():
    inform_data = {}
    response_d = requests.get(INFORM_API_ENDPOINT)
    response_d.raise_for_status()
    response_d = response_d.json()

    for index, i_data in enumerate(response_d):
        iso3 = i_data['Iso3']
        pcountry = get_country_by_iso3(iso3)
        if pcountry is None:
            continue

        indicator_id = i_data['IndicatorId']
        score = i_data['IndicatorScore']
        entry = {
            'id': index + 1,
            'indicator': indicator_id,
            'group': InformIndicator.get_group(indicator_id),
            'score': score,

            'indicator_display': InformIndicator.LABEL_MAP.get(indicator_id),
            'group_display': InformIndicator.get_group_display(indicator_id),
        }

        # Assuming indicator data are unique from the API
        if inform_data.get(pcountry.alpha_2) is None:
            inform_data[pcountry.alpha_2] = [entry]
        else:
            inform_data[pcountry.alpha_2].append(entry)

    return inform_data, len(inform_data), INFORM_API_ENDPOINT


@catch_error()
def load(country, overview, inform_data):
    if country.iso is None or inform_data is None or inform_data.get(country.iso.upper()) is None:
        return

    overview.inform_indicators = inform_data[country.iso.upper()]
    overview.save()
