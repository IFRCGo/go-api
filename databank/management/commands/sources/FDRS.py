import logging

import requests
from django.conf import settings

from databank.models import CountryOverview as CO

from .utils import catch_error

logger = logging.getLogger(__name__)


FDRS_INDICATORS_FIELD_MAP = (
    # INFORM API Indicator, Databank Field
    # Country Key Indicators
    ("Population", CO.population),
    ("UrbPop", CO.urban_population),
    ("GDP", CO.gdp),
    ("GNIPC", CO.gnipc),
    ("Poverty", CO.poverty),
    ("LifeExp", CO.life_expectancy),
    ("Literacy", CO.literacy),
    # National Society Indicators (Using Script: FDRS API)
    ("KPI_IncomeLC_CHF", CO.income),
    ("KPI_expenditureLC_CHF", CO.expenditures),
    ("KPI_PeopleVol_Tot", CO.volunteers),
    ("KPI_TrainFA_Tot", CO.trained_in_first_aid),
    ("KPI_noBranches", CO.branches),
    # volunteers
    ("KPI_PeopleVol_M_age_13_17", CO.male_volunteer_age_13_17),
    ("KPI_PeopleVol_M_age_18_29", CO.male_volunteer_age_18_29),
    ("KPI_PeopleVol_M_age_18_49", CO.male_volunteer_age_18_49),
    ("KPI_PeopleVol_M_age_30_39", CO.male_volunteer_age_30_39),
    ("KPI_PeopleVol_M_age_40_49", CO.male_volunteer_age_40_49),
    ("KPI_PeopleVol_M_age_50_59", CO.male_volunteer_age_50_59),
    ("KPI_PeopleVol_M_age_6_12", CO.male_volunteer_age_6_12),
    ("KPI_PeopleVol_M_age_60_69", CO.male_volunteer_age_60_69),
    ("KPI_PeopleVol_M_age_70_79", CO.male_volunteer_age_70_79),
    ("KPI_PeopleVol_M_age_80", CO.male_volunteer_age_80),
    ("KPI_PeopleVol_M_age_Other", CO.male_volunteer_age_other),
    ("KPI_PeopleVol_Tot_M", CO.male_volunteer_total),
    ("KPI_PeopleVol_F_age_13_17", CO.female_volunteer_age_13_17),
    ("KPI_PeopleVol_F_age_18_29", CO.female_volunteer_age_18_29),
    ("KPI_PeopleVol_F_age_18_49", CO.female_volunteer_age_18_49),
    ("KPI_PeopleVol_F_age_30_39", CO.female_volunteer_age_30_39),
    ("KPI_PeopleVol_F_age_40_49", CO.female_volunteer_age_40_49),
    ("KPI_PeopleVol_F_age_50_59", CO.female_volunteer_age_50_59),
    ("KPI_PeopleVol_F_age_6_12", CO.female_volunteer_age_6_12),
    ("KPI_PeopleVol_F_age_60_69", CO.female_volunteer_age_60_69),
    ("KPI_PeopleVol_F_age_70_79", CO.female_volunteer_age_70_79),
    ("KPI_PeopleVol_F_age_80", CO.female_volunteer_age_80),
    ("KPI_PeopleVol_F_age_Other", CO.female_volunteer_age_other),
    ("KPI_PeopleVol_Tot_F", CO.female_volunteer_total),
    ("KPI_PeopleVol_Tot", CO.volunteer_total),
    ("KPI_PeopleVol_Tot_age_6_12", CO.volunteer_age_6_12),
    ("KPI_PeopleVol_Tot_age_13_17", CO.volunteer_age_13_17),
    ("KPI_PeopleVol_Tot_age_18_29", CO.volunteer_age_18_29),
    # Staff
    ("KPI_PStaff_M_age_18_29", CO.male_staff_age_18_29),
    ("KPI_PStaff_M_age_18_49", CO.male_staff_age_18_49),
    ("KPI_PStaff_M_age_30_39", CO.male_staff_age_30_39),
    ("KPI_PStaff_M_age_40_49", CO.male_staff_age_40_49),
    ("KPI_PStaff_M_age_50_59", CO.male_staff_age_50_59),
    ("KPI_PStaff_M_age_60_69", CO.male_staff_age_60_69),
    ("KPI_PStaff_M_age_70_79", CO.male_staff_age_70_79),
    ("KPI_PStaff_M_age_80", CO.male_staff_age_80),
    ("KPI_PStaff_M_age_Other", CO.male_staff_age_other),
    ("KPI_PStaff_Tot_M", CO.male_staff_total),
    ("KPI_PStaff_F_age_18_29", CO.female_staff_age_18_29),
    ("KPI_PStaff_F_age_18_49", CO.female_staff_age_18_49),
    ("KPI_PStaff_F_age_30_39", CO.female_staff_age_30_39),
    ("KPI_PStaff_F_age_40_49", CO.female_staff_age_40_49),
    ("KPI_PStaff_F_age_50_59", CO.female_staff_age_50_59),
    ("KPI_PStaff_F_age_60_69", CO.female_staff_age_60_69),
    ("KPI_PStaff_F_age_70_79", CO.female_staff_age_70_79),
    ("KPI_PStaff_F_age_80", CO.female_staff_age_80),
    ("KPI_PStaff_F_age_Other", CO.female_staff_age_other),
    ("KPI_PStaff_Tot_F", CO.female_staff_total),
    ("KPI_PStaff_Tot", CO.staff_total),
    ("KPI_PStaff_Tot_age_18_29", CO.staff_age_18_29),
)
FDRS_INDICATORS = [indicator for indicator, _ in FDRS_INDICATORS_FIELD_MAP]

# To fetch NS ID
FDRS_NS_API_ENDPOINT = f"https://data-api.ifrc.org/api/entities/ns?apiKey={settings.FDRS_APIKEY}"

# To fetch NS Data using NS ID
FDRS_DATA_API_ENDPOINT = f"https://data-api.ifrc.org/api/data?apiKey={settings.FDRS_APIKEY}&indicator=" + ",".join(
    FDRS_INDICATORS
)


@catch_error("Error occured while fetching from FDRS API.")
def prefetch():
    fdrs_entities = requests.get(FDRS_NS_API_ENDPOINT)
    if fdrs_entities.status_code != 200:
        return
    fdrs_entities.raise_for_status()
    fdrs_entities = fdrs_entities.json()

    ns_iso_map = {
        # ISO3 are missing for some in FDRS & IFRC-GO only have ISO2 for countries
        ns["KPI_DON_code"]: ns["iso_2"]
        for ns in fdrs_entities
    }

    return (
        {
            # KEY <ISO2>-<Indicator_ID>: {year: '', value: ''}
            # NOTE: We are fetching the latest data for each indicators
            f"{ns_iso_map[ns_data['id']].upper()}-{indicator_data['id']}": (
                max(ns_data["data"], key=lambda x: x["year"]) if (ns_data["data"] and len(ns_data["data"]) > 0) else None
            )
            for indicator_data in requests.get(FDRS_DATA_API_ENDPOINT).json()["data"]
            for ns_data in indicator_data["data"]
        },
        len(ns_iso_map),
        FDRS_DATA_API_ENDPOINT,
    )


@catch_error()
def load(country, overview, fdrs_data):
    if country.iso is None or fdrs_data is None:
        return

    fdrs_data_fetched_year = max(
        int(item["year"]) for item in fdrs_data.values() if item is not None and item.get("year") is not None
    )

    # NOTE: We are getting the only latest year specific data
    for fdrs_indicator, field in FDRS_INDICATORS_FIELD_MAP:
        data = fdrs_data.get(f"{country.iso.upper()}-{fdrs_indicator}")
        value = None
        if data and int(data.get("year")) == fdrs_data_fetched_year:
            value = data.get("value")
        setattr(overview, field.field.name, value)
    overview.fdrs_data_fetched_year = str(fdrs_data_fetched_year)
    overview.save()
