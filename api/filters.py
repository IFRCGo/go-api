import strawberry
import typing
import strawberry_django
from django.db import models

from .enums import AppealStatusEnum, AppealTypeEnum
from .models import Appeal


@strawberry_django.filters.filter(Appeal, lookups=True)
class AppealFilter:
    id: strawberry.auto

    atype: typing.Optional[AppealTypeEnum]  # type: ignore[reportInvalidTypeForm]
    dtype_id: strawberry.auto
    country_id: strawberry.auto
    region_id: strawberry.auto
    code: strawberry.auto
    status: typing.Optional[AppealStatusEnum]  # type: ignore[reportInvalidTypeForm]
    id: strawberry.auto
    appeal_id: strawberry.auto

    @strawberry_django.filter_field
    def districts(
        self,
        queryset: models.QuerySet,
        value: list[strawberry.ID],
        prefix: str,
    ) -> tuple[models.QuerySet, models.Q]:
        return queryset, models.Q(**{f"{prefix}country__district__in": value})

    @strawberry_django.filter_field
    def admin2s(
        self,
        queryset: models.QuerySet,
        value: list[strawberry.ID],
        prefix: str,
    ) -> tuple[models.QuerySet, models.Q]:
        return queryset, models.Q(**{f"{prefix}country__district__admin2__in": value})
