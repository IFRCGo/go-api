from django_filters import rest_framework as filters

from .models import DelegationOffice, ExternallyManagedLocalUnit, LocalUnit


class LocalUnitFilters(filters.FilterSet):
    status = filters.ChoiceFilter(
        choices=LocalUnit.Status.choices,
        label="Status",
    )

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
            "status",
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
        fields = {
            "country__name": ["exact", "in"],
            "country__iso3": ["exact", "in"],
            "country__iso": ["exact", "in"],
            "country__id": ["exact", "in"],
        }
