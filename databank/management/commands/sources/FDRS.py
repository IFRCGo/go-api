import logging

import requests
from django.conf import settings

from databank.models import CountryOverview as CO

from .utils import catch_error

logger = logging.getLogger(__name__)


FDRS_INDICATORS_FIELD_MAP = {
    # INFORM API Indicator, Databank Field
    # Country Key Indicators
    "Population": (CO.fdrs_population, CO.fdrs_population_data_year),
    "UrbPop": (CO.fdrs_urban_population, CO.fdrs_urban_population_data_year),
    "GDP": (CO.fdrs_gdp, CO.fdrs_gdp_data_year),
    "GNIPC": (CO.fdrs_gnipc, CO.fdrs_gnipc_data_year),
    "Poverty": (CO.fdrs_poverty, CO.fdrs_poverty_data_year),
    "LifeExp": (CO.fdrs_life_expectancy, CO.fdrs_life_expectancy_data_year),
    "Literacy": (CO.fdrs_literacy, CO.fdrs_literacy_data_year),
    # National Society Indicators (Using Script: FDRS API)
    "KPI_IncomeLC_CHF": (CO.fdrs_income, CO.fdrs_income_data_year),
    "KPI_expenditureLC_CHF": (CO.fdrs_expenditures, CO.fdrs_expenditures_data_year),
    "KPI_TrainFA_Tot": (CO.fdrs_trained_in_first_aid, CO.fdrs_trained_in_first_aid_data_year),
    "KPI_noBranches": (CO.fdrs_branches, CO.fdrs_branches_data_year),
}

FDRS_VOLUNTEERS_DISAGGREGATION_INDICATORS_FIELD_MAP = (
    # volunteers
    ("KPI_PeopleVol_M_age_13_17", CO.fdrs_male_volunteer_age_13_17),
    ("KPI_PeopleVol_M_age_18_29", CO.fdrs_male_volunteer_age_18_29),
    ("KPI_PeopleVol_M_age_18_49", CO.fdrs_male_volunteer_age_18_49),
    ("KPI_PeopleVol_M_age_30_39", CO.fdrs_male_volunteer_age_30_39),
    ("KPI_PeopleVol_M_age_40_49", CO.fdrs_male_volunteer_age_40_49),
    ("KPI_PeopleVol_M_age_50_59", CO.fdrs_male_volunteer_age_50_59),
    ("KPI_PeopleVol_M_age_6_12", CO.fdrs_male_volunteer_age_6_12),
    ("KPI_PeopleVol_M_age_60_69", CO.fdrs_male_volunteer_age_60_69),
    ("KPI_PeopleVol_M_age_70_79", CO.fdrs_male_volunteer_age_70_79),
    ("KPI_PeopleVol_M_age_80", CO.fdrs_male_volunteer_age_80),
    ("KPI_PeopleVol_M_age_Other", CO.fdrs_male_volunteer_age_other),
    ("KPI_PeopleVol_Tot_M", CO.fdrs_male_volunteer_total),
    ("KPI_PeopleVol_F_age_13_17", CO.fdrs_female_volunteer_age_13_17),
    ("KPI_PeopleVol_F_age_18_29", CO.fdrs_female_volunteer_age_18_29),
    ("KPI_PeopleVol_F_age_18_49", CO.fdrs_female_volunteer_age_18_49),
    ("KPI_PeopleVol_F_age_30_39", CO.fdrs_female_volunteer_age_30_39),
    ("KPI_PeopleVol_F_age_40_49", CO.fdrs_female_volunteer_age_40_49),
    ("KPI_PeopleVol_F_age_50_59", CO.fdrs_female_volunteer_age_50_59),
    ("KPI_PeopleVol_F_age_6_12", CO.fdrs_female_volunteer_age_6_12),
    ("KPI_PeopleVol_F_age_60_69", CO.fdrs_female_volunteer_age_60_69),
    ("KPI_PeopleVol_F_age_70_79", CO.fdrs_female_volunteer_age_70_79),
    ("KPI_PeopleVol_F_age_80", CO.fdrs_female_volunteer_age_80),
    ("KPI_PeopleVol_F_age_Other", CO.fdrs_female_volunteer_age_other),
    ("KPI_PeopleVol_Tot_F", CO.fdrs_female_volunteer_total),
    ("KPI_PeopleVol_Tot", CO.fdrs_volunteer_total),
    ("KPI_PeopleVol_Tot_age_6_12", CO.fdrs_volunteer_age_6_12),
    ("KPI_PeopleVol_Tot_age_13_17", CO.fdrs_volunteer_age_13_17),
    ("KPI_PeopleVol_Tot_age_18_29", CO.fdrs_volunteer_age_18_29),
)

FDRS_STAFF_DISAGGREGATION_INDICATORS_FIELD_MAP = (
    # Staff
    ("KPI_PStaff_M_age_18_29", CO.fdrs_male_staff_age_18_29),
    ("KPI_PStaff_M_age_18_49", CO.fdrs_male_staff_age_18_49),
    ("KPI_PStaff_M_age_30_39", CO.fdrs_male_staff_age_30_39),
    ("KPI_PStaff_M_age_40_49", CO.fdrs_male_staff_age_40_49),
    ("KPI_PStaff_M_age_50_59", CO.fdrs_male_staff_age_50_59),
    ("KPI_PStaff_M_age_60_69", CO.fdrs_male_staff_age_60_69),
    ("KPI_PStaff_M_age_70_79", CO.fdrs_male_staff_age_70_79),
    ("KPI_PStaff_M_age_80", CO.fdrs_male_staff_age_80),
    ("KPI_PStaff_M_age_Other", CO.fdrs_male_staff_age_other),
    ("KPI_PStaff_Tot_M", CO.fdrs_male_staff_total),
    ("KPI_PStaff_F_age_18_29", CO.fdrs_female_staff_age_18_29),
    ("KPI_PStaff_F_age_18_49", CO.fdrs_female_staff_age_18_49),
    ("KPI_PStaff_F_age_30_39", CO.fdrs_female_staff_age_30_39),
    ("KPI_PStaff_F_age_40_49", CO.fdrs_female_staff_age_40_49),
    ("KPI_PStaff_F_age_50_59", CO.fdrs_female_staff_age_50_59),
    ("KPI_PStaff_F_age_60_69", CO.fdrs_female_staff_age_60_69),
    ("KPI_PStaff_F_age_70_79", CO.fdrs_female_staff_age_70_79),
    ("KPI_PStaff_F_age_80", CO.fdrs_female_staff_age_80),
    ("KPI_PStaff_F_age_Other", CO.fdrs_female_staff_age_other),
    ("KPI_PStaff_Tot_F", CO.fdrs_female_staff_total),
    ("KPI_PStaff_Tot", CO.fdrs_staff_total),
    ("KPI_PStaff_Tot_age_18_29", CO.fdrs_staff_age_18_29),
)
FDRS_INDICATORS = (
    [indicator for indicator in FDRS_INDICATORS_FIELD_MAP.keys()]
    + [indicator for indicator, _ in FDRS_VOLUNTEERS_DISAGGREGATION_INDICATORS_FIELD_MAP]
    + [indicator for indicator, _ in FDRS_STAFF_DISAGGREGATION_INDICATORS_FIELD_MAP]
)


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

    for indicator, (field, year_field) in FDRS_INDICATORS_FIELD_MAP.items():
        data = fdrs_data.get(f"{country.iso.upper()}-{indicator}")
        if data:
            setattr(overview, field.field.name, data.get("value"))
            setattr(overview, year_field.field.name, data.get("year"))

    def set_disaggregation_data(disaggregation_map, data_year_field):
        """
        Set disaggregation data for volunteers or staff for the latest year
        """
        latest_year = None
        for indicator, field in disaggregation_map:
            data = fdrs_data.get(f"{country.iso.upper()}-{indicator}")
            if data:
                year = data.get("year")
                if latest_year is None or (year and int(year) > latest_year):
                    latest_year = int(year)
                setattr(overview, field.field.name, data.get("value"))
        setattr(overview, data_year_field.field.name, latest_year)

    # Volunteer disaggregation
    set_disaggregation_data(FDRS_VOLUNTEERS_DISAGGREGATION_INDICATORS_FIELD_MAP, CO.fdrs_volunteer_data_year)
    # Staff disaggregation
    set_disaggregation_data(FDRS_STAFF_DISAGGREGATION_INDICATORS_FIELD_MAP, CO.fdrs_staff_data_year)

    overview.save()
