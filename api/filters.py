import strawberry
import strawberry_django
from django.db import models

from .models import District


@strawberry_django.filters.filter(District, lookups=True)
class DistrictFilter:
    id: strawberry.auto
    country: strawberry.auto

    @strawberry_django.filter_field
    def unknown(
        self,
        queryset: models.QuerySet,
        value: bool,
        prefix: str,
    ) -> tuple[models.QuerySet, models.Q]:
        if value:
            return queryset, models.Q(**{f"{prefix}id__lt": 0})
        return queryset, models.Q(**{f"{prefix}id__gte": 0})
