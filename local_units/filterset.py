from django_filters import rest_framework as filters

from .models import DelegationOffice, LocalUnit


class LocalUnitFilters(filters.FilterSet):
    class Meta:
        model = LocalUnit
        fields = (
            "country__name",
            "country__iso3",
            "country__iso",
            "type__code",
            "draft",
            "validated",
        )


class DelegationOfficeFilters(filters.FilterSet):
    class Meta:
        model = DelegationOffice
        fields = (
            "country__name",
            "country__iso3",
            "country__iso",
            "dotype__code",
        )
