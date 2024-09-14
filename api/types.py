import typing

import strawberry_django
from django.db import models
from strawberry import ID, auto

from local_units.models import DelegationOffice
from main.context import Info
from utils.common import get_queryset_for_model
from utils.types import PolygonScalar, string_field

from .models import Admin2, Country, CountryDirectory, District


@strawberry_django.type(Country)
class CountryType:
    id: ID
    links: auto
    contacts: auto
    name: auto
    iso: auto
    iso3: auto
    society_name: auto
    society_url: auto
    region: auto
    overview: auto
    key_priorities: auto
    inform_score: auto
    id: auto
    url_ifrc: auto
    additional_tab_name: auto
    nsi_income: auto
    nsi_expenditures: auto
    nsi_branches: auto
    nsi_staff: auto
    nsi_volunteers: auto
    nsi_youth: auto
    nsi_trained_in_first_aid: auto
    nsi_gov_financial_support: auto
    nsi_domestically_generated_income: auto
    nsi_annual_fdrs_reporting: auto
    nsi_policy_implementation: auto
    nsi_risk_management_framework: auto
    nsi_cmc_dashboard_compliance: auto
    wash_kit2: auto
    wash_kit5: auto
    wash_kit10: auto
    wash_staff_at_hq: auto
    wash_staff_at_branch: auto
    wash_ndrt_trained: auto
    wash_rdrt_trained: auto
    bbox: PolygonScalar | None
    centroid: PolygonScalar | None
    fdrs: auto
    address_1: auto
    address_2: auto
    city_code: auto
    phone: auto
    website: auto
    emails: auto
    countrydirectory_set: list["DirectoryType"]
    delegation_office_country: list["DelegationOfficeType"]
    # initiatives: auto
    # capacity: auto
    # organizational_capacity: auto
    # icrc_presence: auto
    # disaster_law_url: auto

    @staticmethod
    def get_queryset(_, queryset: models.QuerySet, info: Info | None):
        return get_queryset_for_model(Country, queryset)


@strawberry_django.type(CountryDirectory)
class DirectoryType:
    id: ID
    first_name: auto
    last_name: auto
    position: auto


@strawberry_django.type(DelegationOffice)
class DelegationOfficeType:
    id: ID
    name: auto
    city: auto
    address: auto
    postcode: auto
    location: auto
    society_url: auto
    url_ifrc: auto
    hod_first_name: auto
    hod_last_name: auto
    hod_mobile_number: auto
    hod_email: auto
    assistant_name: auto
    assistant_email: auto
    is_ns_same_location: auto
    is_multiple_ifrc_offices: auto
    visibility: auto
    created_at: auto
    modified_at: auto
    date_of_data: auto
    # dotype: auto  # delegation_office_type FIXME


@strawberry_django.type(District)
class DistrictType:
    id: ID
    name = string_field(District.name)
    bbox: PolygonScalar | None

    if typing.TYPE_CHECKING:
        country_id = District.country_id
        pk = District.pk
    else:
        country_id: ID

    @staticmethod
    def get_queryset(_, queryset: models.QuerySet, info: Info | None):
        return get_queryset_for_model(District, queryset).defer("centroid")


@strawberry_django.type(Admin2)
class Admin2Type:
    id: ID
    name = string_field(Admin2.name)
    created_at = string_field(Admin2.created_at)
    bbox: PolygonScalar | None

    if typing.TYPE_CHECKING:
        admin1_id = Admin2.admin1_id
        pk = Admin2.pk
    else:
        admin1_id: ID

    @staticmethod
    def get_queryset(_, queryset: models.QuerySet, info: Info | None):
        return get_queryset_for_model(Admin2, queryset).defer("centroid")
