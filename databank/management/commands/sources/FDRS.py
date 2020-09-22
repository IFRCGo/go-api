import logging
import requests
from django.conf import settings

from databank.models import CountryOverview as CO
from .utils import catch_error

logger = logging.getLogger(__name__)


FDRS_INDICATORS_FIELD_MAP = (
    # INFORM API Indicator, Databank Field
    # Country Key Indicators
    ('Population', CO.population),
    ('UrbPop', CO.urban_population),
    ('GDP', CO.gdp),
    ('GNIPC', CO.gnipc),
    ('Poverty', CO.poverty),
    ('LifeExp', CO.life_expectancy),
    ('Literacy', CO.literacy),

    # National Society Indicators (Using Script: FDRS API)
    ('KPI_IncomeLC_CHF', CO.income),
    ('KPI_expenditureLC_CHF', CO.expenditures),
    ('KPI_PeopleVol_Tot', CO.volunteers),
    ('KPI_TrainFA_Tot', CO.trained_in_first_aid),
)
FDRS_INDICATORS = [indicator for indicator, _ in FDRS_INDICATORS_FIELD_MAP]

# To fetch NS ID
FDRS_NS_API_ENDPOINT = f'https://data-api.ifrc.org/api/entities/ns?apiKey={settings.FDRS_APIKEY}'

# To fetch NS Data using NS ID
FDRS_DATA_API_ENDPOINT = f'https://data-api.ifrc.org/api/data?apiKey={settings.FDRS_APIKEY}&indicator=' + ','.join(FDRS_INDICATORS)


@catch_error('Error occured while fetching from FDRS API.')
def prefetch():
    fdrs_entities = requests.get(FDRS_NS_API_ENDPOINT)
    fdrs_entities.raise_for_status()
    fdrs_entities = fdrs_entities.json()

    ns_iso_map = {
        # ISO3 are missing for some in FDRS & IFRC-GO only have ISO2 for countries
        ns['KPI_DON_code']: ns['iso_2']
        for ns in fdrs_entities
    }

    return {
        # KEY <ISO2>-<Indicator_ID>: {year: '', value: ''}
        f"{ns_iso_map[ns_data['id']].upper()}-{indicator_data['id']}": (
            ns_data['data'][-1] if (
                ns_data['data'] and len(ns_data['data']) > 0
            ) else None
        )
        for indicator_data in requests.get(FDRS_DATA_API_ENDPOINT).json()['data']
        for ns_data in indicator_data['data']
    }, len(ns_iso_map), FDRS_DATA_API_ENDPOINT


@catch_error()
def load(country, overview, fdrs_data):
    if fdrs_data is None:
        return

    for fdrs_indicator, field in FDRS_INDICATORS_FIELD_MAP:
        value = fdrs_data.get(f'{country.iso.upper()}-{fdrs_indicator}')
        setattr(
            overview,
            field.field_name,
            value and value['value'],
        )
    overview.save()
