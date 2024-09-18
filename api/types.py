import typing

import strawberry
import strawberry_django
from django.db import models

from utils.common import get_queryset_for_model
from utils.strawberry.enums import enum_field, enum_display_field
from main.graphql.context import Info

from .models import Appeal


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

    shelter_num_people_targeted: strawberry.auto
    shelter_num_people_reached: strawberry.auto
    shelter_budget: strawberry.auto

    basic_needs_num_people_targeted: strawberry.auto
    basic_needs_num_people_reached: strawberry.auto
    basic_needs_budget: strawberry.auto

    health_num_people_targeted: strawberry.auto
    health_num_people_reached: strawberry.auto
    health_budget: strawberry.auto

    water_sanitation_num_people_targeted: strawberry.auto
    water_sanitation_num_people_reached: strawberry.auto
    water_sanitation_budget: strawberry.auto

    gender_inclusion_num_people_targeted: strawberry.auto
    gender_inclusion_num_people_reached: strawberry.auto
    gender_inclusion_budget: strawberry.auto

    migration_num_people_targeted: strawberry.auto
    migration_num_people_reached: strawberry.auto
    migration_budget: strawberry.auto

    risk_reduction_num_people_targeted: strawberry.auto
    risk_reduction_num_people_reached: strawberry.auto
    risk_reduction_budget: strawberry.auto

    strenghtening_national_society_budget: strawberry.auto
    international_disaster_response_budget: strawberry.auto
    influence_budget: strawberry.auto
    accountable_ifrc_budget: strawberry.auto

    triggering_amount: strawberry.auto

    @staticmethod
    def get_queryset(_, queryset: models.QuerySet | None, info: Info):
        return get_queryset_for_model(Appeal, queryset)

    # @strawberry_django.field
    # async def dtype(self, root: Appeal, info: Info) -> ProjectType:
    #     return await info.context.dl.api.load_disaster.load(root.dtype_id)

    # TODO: Using dataloader
    # - region
    # - event
    # - country
