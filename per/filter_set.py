import django_filters as filters

from per.models import (
    Overview,
    FormPrioritization,
    PerWorkPlan,
)
from api.models import Country


class PerOverviewFilter(filters.FilterSet):
    country = filters.ModelMultipleChoiceFilter(field_name="country", queryset=Country.objects.all())

    class Meta:
        model = Overview
        fields = ()


class PerPrioritizationFilter(filters.FilterSet):
    component = filters.NumberFilter(field_name="overview_id", lookup_expr="exact")

    class Meta:
        model = FormPrioritization
        fields = ()


class PerWorkPlanFilter(filters.FilterSet):
    component = filters.NumberFilter(field_name="overview_id", lookup_expr="exact")

    class Meta:
        model = PerWorkPlan
        fields = ()
