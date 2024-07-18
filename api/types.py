# from typing import List, Optional
import strawberry_django

# from django.contrib.auth import get_user_model
from django.db.models import Q
from strawberry import auto

from . import models


@strawberry_django.filters.filter(models.Country, lookups=True)
class CountryFilter:
    id: auto
    name: auto

    @strawberry_django.filter_field
    def filter(self, prefix, queryset):
        return queryset, Q()


@strawberry_django.type(
    models.Country,
    filters=CountryFilter,
    pagination=True,
)
class Country:
    id: auto
    name: auto
