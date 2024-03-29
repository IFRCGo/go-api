from django_filters import rest_framework as filters

from .models import LocalUnit


class LocalUnitFilters(filters.FilterSet):
    class Meta:
        model = LocalUnit
        fields = (
            'country__name',
            'country__iso3',
            'country__iso',
            'type__code',
            'draft',
            'validated',
        )
