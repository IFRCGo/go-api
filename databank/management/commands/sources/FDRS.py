import logging
from typing import List, Optional, Tuple

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
    list(FDRS_INDICATORS_FIELD_MAP.keys())
    + [indicator for indicator, _ in FDRS_VOLUNTEERS_DISAGGREGATION_INDICATORS_FIELD_MAP]
    + [indicator for indicator, _ in FDRS_STAFF_DISAGGREGATION_INDICATORS_FIELD_MAP]
)


# To fetch NS ID
FDRS_NS_API_ENDPOINT = f"https://data-api.ifrc.org/api/entities/ns?apiKey={settings.FDRS_APIKEY}"

# To fetch NS Data using NS ID
FDRS_DATA_API_ENDPOINT = f"https://data-api.ifrc.org/api/data?apiKey={settings.FDRS_APIKEY}&indicator=" + ",".join(
    FDRS_INDICATORS
)


@catch_error("Error occurred while fetching from FDRS API.")
def prefetch():
    response = requests.get(FDRS_NS_API_ENDPOINT)
    response.raise_for_status()
    fdrs_entities = response.json()

    ns_iso_map = {ns["KPI_DON_code"]: ns["iso_2"] for ns in fdrs_entities}

    fdrs_data_response = requests.get(FDRS_DATA_API_ENDPOINT)
    fdrs_data_response.raise_for_status()
    fdrs_data = fdrs_data_response.json()["data"]

    # Getting the latest available data for the indicators
    processed_fdrs_data = {}

    for indictor_data in fdrs_data:
        indicator_id = indictor_data["id"]

        for ns_data in indictor_data["data"]:
            ns_id = ns_data["id"]
            iso_code = ns_iso_map.get(ns_id)

            if not iso_code:
                continue

            latest_data_with_value = None
            for data in ns_data["data"]:
                if data.get("value"):
                    if latest_data_with_value is None or int(data["year"]) > int(latest_data_with_value["year"]):
                        latest_data_with_value = data

            if latest_data_with_value:
                processed_fdrs_data[f"{iso_code}-{indicator_id}"] = latest_data_with_value

    return (processed_fdrs_data, len(ns_iso_map), FDRS_DATA_API_ENDPOINT)


def set_latest_year_data(
    disaggregation_map: List[Tuple[str, CO]],
    data_year_field: CO,
    latest_year: int,
    fdrs_data: dict,
    country_iso: str,
    overview: CO,
) -> None:
    """
    Set only the latest year data for volunteers or staff for the provided year
    """
    for indicator, field in disaggregation_map:
        data = fdrs_data.get(f"{country_iso}-{indicator}")
        if data and int(data.get("year")) == latest_year:
            setattr(overview, field.field.name, data.get("value"))

    # Set the year field for the data
    setattr(overview, data_year_field.field.name, latest_year)


def get_latest_year_from_indicators(disaggregation_map: List[Tuple[str, CO]], fdrs_data: dict, country_iso: str) -> Optional[int]:
    """
    Get the latest year across all indicators where the value field exists
    """
    return max(
        (
            int(data["year"])
            for indicator, _ in disaggregation_map
            if (data := fdrs_data.get(f"{country_iso}-{indicator}")) and data.get("value")
        ),
        default=None,
    )


@catch_error("Error occurred while loading FDRS data.")
def load(country, overview, fdrs_data):
    if not country.iso or not fdrs_data:
        return

    country_iso = country.iso.upper()

    # Country Key Indicators
    for indicator, (field, year_field) in FDRS_INDICATORS_FIELD_MAP.items():
        data = fdrs_data.get(f"{country_iso}-{indicator}")
        if data:
            setattr(overview, field.field.name, data.get("value"))
            setattr(overview, year_field.field.name, data.get("year"))

    # Volunteer disaggregation data
    latest_year = get_latest_year_from_indicators(
        disaggregation_map=FDRS_VOLUNTEERS_DISAGGREGATION_INDICATORS_FIELD_MAP, fdrs_data=fdrs_data, country_iso=country_iso
    )
    if latest_year:
        set_latest_year_data(
            disaggregation_map=FDRS_VOLUNTEERS_DISAGGREGATION_INDICATORS_FIELD_MAP,
            data_year_field=CO.fdrs_volunteer_data_year,
            latest_year=latest_year,
            fdrs_data=fdrs_data,
            country_iso=country_iso,
            overview=overview,
        )

    # Staff disaggregation data
    latest_year = get_latest_year_from_indicators(
        disaggregation_map=FDRS_STAFF_DISAGGREGATION_INDICATORS_FIELD_MAP, fdrs_data=fdrs_data, country_iso=country_iso
    )
    if latest_year:
        set_latest_year_data(
            disaggregation_map=FDRS_STAFF_DISAGGREGATION_INDICATORS_FIELD_MAP,
            data_year_field=CO.fdrs_staff_data_year,
            latest_year=latest_year,
            fdrs_data=fdrs_data,
            country_iso=country_iso,
            overview=overview,
        )

    overview.save()
