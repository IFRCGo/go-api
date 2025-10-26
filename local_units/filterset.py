from django_filters import rest_framework as filters

from .models import (
    DelegationOffice,
    ExternallyManagedLocalUnit,
    LocalUnit,
    LocalUnitBulkUpload,
)


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


class LocalUnitBulkUploadFilters(filters.FilterSet):
    class Meta:
        model = LocalUnitBulkUpload
        fields = {
            "country__name": ["exact", "in"],
            "country__iso3": ["exact", "in"],
            "country__iso": ["exact", "in"],
            "country__id": ["exact", "in"],
        }


class HealthLocalUnitFilters(filters.FilterSet):
    # Simple filters for health-local-units endpoint
    region = filters.NumberFilter(field_name="country__region_id", label="Region")
    country = filters.NumberFilter(field_name="country_id", label="Country")
    iso3 = filters.CharFilter(field_name="country__iso3", lookup_expr="exact", label="ISO3")
    validated = filters.BooleanFilter(method="filter_validated", label="Validated")
    subtype = filters.CharFilter(field_name="subtype", lookup_expr="icontains", label="Subtype")

    class Meta:
        model = LocalUnit
        fields = (
            "region",
            "country",
            "iso3",
            "validated",
            "subtype",
        )

    def filter_validated(self, queryset, name, value):
        if value is True:
            return queryset.filter(status=LocalUnit.Status.VALIDATED)
        if value is False:
            return queryset.exclude(status=LocalUnit.Status.VALIDATED)
        return queryset
