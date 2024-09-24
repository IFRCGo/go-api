import typing

import strawberry
import strawberry_django
from django.db import models

from utils.common import get_queryset_for_model
from utils.strawberry.enums import enum_field, enum_display_field
from main.graphql.context import Info

from .models import Appeal, Country, DisasterType


@strawberry_django.type(DisasterType)
class DisasterTypeType:
    id: strawberry.ID

    name: strawberry.auto
    summary: strawberry.auto


@strawberry_django.type(Country)
class CountryType:
    id: strawberry.ID

    name: strawberry.auto
    record_type = enum_field(Country.record_type)
    record_type_display = enum_display_field(Country.record_type)

    iso: strawberry.auto
    iso3: strawberry.auto
    fdrs: strawberry.auto
    society_name: strawberry.auto
    society_url: strawberry.auto
    url_ifrc: strawberry.auto
    region_id: typing.Optional[strawberry.ID]
    overview: strawberry.auto
    key_priorities: strawberry.auto
    inform_score: strawberry.auto

    # logo = models.FileField()

    centroid: strawberry.auto
    bbox: strawberry.auto
    independent: strawberry.auto
    is_deprecated: strawberry.auto
    sovereign_state_id: typing.Optional[strawberry.ID]
    disputed: strawberry.auto

    # Population Data From WB API
    wb_population: strawberry.auto
    wb_year: strawberry.auto
    additional_tab_name: strawberry.auto

    # Additional NS Indicator fields
    nsi_income: strawberry.auto
    nsi_expenditures: strawberry.auto
    nsi_branches: strawberry.auto
    nsi_staff: strawberry.auto
    nsi_volunteers: strawberry.auto
    nsi_youth: strawberry.auto
    nsi_trained_in_first_aid: strawberry.auto
    nsi_gov_financial_support: strawberry.auto
    nsi_domestically_generated_income: strawberry.auto
    nsi_annual_fdrs_reporting: strawberry.auto
    nsi_policy_implementation: strawberry.auto
    nsi_risk_management_framework: strawberry.auto
    nsi_cmc_dashboard_compliance: strawberry.auto

    # WASH Capacity Indicators
    wash_total_staff: strawberry.auto
    wash_kit2: strawberry.auto
    wash_kit5: strawberry.auto
    wash_kit10: strawberry.auto
    wash_staff_at_hq: strawberry.auto
    wash_staff_at_branch: strawberry.auto
    wash_ndrt_trained: strawberry.auto
    wash_rdrt_trained: strawberry.auto

    in_search: strawberry.auto
    # Used in Emergency Project
    average_household_size: strawberry.auto
    address_1: strawberry.auto
    address_2: strawberry.auto
    city_code: strawberry.auto
    phone: strawberry.auto
    website: strawberry.auto

    emails: typing.Optional[typing.List[str]]
    founded_date: strawberry.auto

    # disaster law url
    disaster_law_url: strawberry.auto


@strawberry_django.type(Appeal)
class AppealType:
    id: strawberry.ID

    aid: strawberry.auto
    name: strawberry.auto
    dtype_id: typing.Optional[strawberry.ID]
    atype = enum_field(Appeal.atype)
    atype_display = enum_display_field(Appeal.atype)

    status = enum_field(Appeal.status)
    status_display = enum_display_field(Appeal.status)
    code: strawberry.auto
    sector: strawberry.auto

    num_beneficiaries: strawberry.auto
    amount_requested: strawberry.auto
    amount_funded: strawberry.auto

    start_date: strawberry.auto
    end_date: strawberry.auto
    created_at: strawberry.auto
    modified_at: strawberry.auto
    previous_update: strawberry.auto
    real_data_update: strawberry.auto

    event: typing.Optional[strawberry.ID]
    needs_confirmation: strawberry.auto
    country_id: strawberry.ID
    region_id: typing.Optional[strawberry.ID]

    # shelter_num_people_targeted: strawberry.auto
    # shelter_num_people_reached: strawberry.auto
    # shelter_budget: strawberry.auto

    # basic_needs_num_people_targeted: strawberry.auto
    # basic_needs_num_people_reached: strawberry.auto
    # basic_needs_budget: strawberry.auto

    # health_num_people_targeted: strawberry.auto
    # health_num_people_reached: strawberry.auto
    # health_budget: strawberry.auto

    # water_sanitation_num_people_targeted: strawberry.auto
    # water_sanitation_num_people_reached: strawberry.auto
    # water_sanitation_budget: strawberry.auto

    # gender_inclusion_num_people_targeted: strawberry.auto
    # gender_inclusion_num_people_reached: strawberry.auto
    # gender_inclusion_budget: strawberry.auto

    # migration_num_people_targeted: strawberry.auto
    # migration_num_people_reached: strawberry.auto
    # migration_budget: strawberry.auto

    # risk_reduction_num_people_targeted: strawberry.auto
    # risk_reduction_num_people_reached: strawberry.auto
    # risk_reduction_budget: strawberry.auto

    # strenghtening_national_society_budget: strawberry.auto
    # international_disaster_response_budget: strawberry.auto
    # influence_budget: strawberry.auto
    # accountable_ifrc_budget: strawberry.auto

    triggering_amount: strawberry.auto

    @staticmethod
    def get_queryset(_, queryset: typing.Optional[models.QuerySet], info: Info):
        return get_queryset_for_model(Appeal, queryset)

    @strawberry_django.field
    async def dtype(self, root: Appeal, info: Info) -> typing.Optional[DisasterTypeType]:
        if root.dtype_id:
            return await info.context.dl.api.load_disaster_type.load(root.dtype_id)

    @strawberry_django.field
    async def country(self, root: Appeal, info: Info) -> CountryType:
        return await info.context.dl.api.load_country.load(root.country_id)

    # TODO: Using dataloader
    # - region
    # - event
    # - country
