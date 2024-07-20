from typing import Optional  # List

import strawberry_django

# from django.contrib.auth import get_user_model
from django.db.models import Q
from strawberry import auto

from . import models

# filters


@strawberry_django.filters.filter(models.Country, lookups=True)
class CountryFilter:
    id: auto
    name: auto
    name_en: Optional[str]
    name_fr: Optional[str]
    name_es: Optional[str]
    name_ar: Optional[str]
    society_name_en: Optional[str]
    society_name_fr: Optional[str]
    society_name_es: Optional[str]
    society_name_ar: Optional[str]
    overview_en: Optional[str]
    overview_fr: Optional[str]
    overview_es: Optional[str]
    overview_ar: Optional[str]
    additional_tab_name_en: Optional[str]
    additional_tab_name_fr: Optional[str]
    additional_tab_name_es: Optional[str]
    additional_tab_name_ar: Optional[str]

    @strawberry_django.filter_field
    def filter(self, prefix, queryset):
        return queryset, Q()


# order


@strawberry_django.ordering.order(models.Country)
class CountryOrder:
    name: auto


# types


@strawberry_django.type(
    models.Country,
    filters=CountryFilter,
    pagination=True,
    fields="__all__",
)
class Country:
    id: auto
    name: auto
    name_en: Optional[str]
    name_fr: Optional[str]
    name_es: Optional[str]
    name_ar: Optional[str]
    society_name_en: Optional[str]
    society_name_fr: Optional[str]
    society_name_es: Optional[str]
    society_name_ar: Optional[str]
    overview_en: Optional[str]
    overview_fr: Optional[str]
    overview_es: Optional[str]
    overview_ar: Optional[str]
    additional_tab_name_en: Optional[str]
    additional_tab_name_fr: Optional[str]
    additional_tab_name_es: Optional[str]
    additional_tab_name_ar: Optional[str]


# input types


@strawberry_django.input(
    models.Country,
    fields="__all__",
)
class CountryInput:
    id: auto
    name: auto
    name_en: Optional[str]
    name_fr: Optional[str]
    name_es: Optional[str]
    name_ar: Optional[str]
    society_name_en: Optional[str]
    society_name_fr: Optional[str]
    society_name_es: Optional[str]
    society_name_ar: Optional[str]
    overview_en: Optional[str]
    overview_fr: Optional[str]
    overview_es: Optional[str]
    overview_ar: Optional[str]
    additional_tab_name_en: Optional[str]
    additional_tab_name_fr: Optional[str]
    additional_tab_name_es: Optional[str]
    additional_tab_name_ar: Optional[str]


@strawberry_django.input(
    models.Country,
    fields="__all__",
    partial=True,
)
class CountryPartialInput(CountryInput):
    id: auto
    name: auto
    name_en: Optional[str]
    name_fr: Optional[str]
    name_es: Optional[str]
    name_ar: Optional[str]
    society_name_en: Optional[str]
    society_name_fr: Optional[str]
    society_name_es: Optional[str]
    society_name_ar: Optional[str]
    overview_en: Optional[str]
    overview_fr: Optional[str]
    overview_es: Optional[str]
    overview_ar: Optional[str]
    additional_tab_name_en: Optional[str]
    additional_tab_name_fr: Optional[str]
    additional_tab_name_es: Optional[str]
    additional_tab_name_ar: Optional[str]
