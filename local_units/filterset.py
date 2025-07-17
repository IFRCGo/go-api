from django_filters import rest_framework as filters

from .models import DelegationOffice, ExternallyManagedLocalUnit, LocalUnit


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
            "is_locked",
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


class ExternallyManagedLocalUnitFilters(filters.FilterSet):
    class Meta:
        model = ExternallyManagedLocalUnit
        fields = (
            "country__name",
            "country__iso3",
            "country__iso",
        )
