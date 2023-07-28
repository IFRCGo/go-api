import django_filters as filters

from per.models import (
    Overview,
    FormPrioritization,
    PerWorkPlan,
    Form,
)
from api.models import Country


class PerOverviewFilter(filters.FilterSet):
    country = filters.ModelMultipleChoiceFilter(field_name="country", queryset=Country.objects.all())
    region = filters.NumberFilter(field_name="country__region")
    class Meta:
        model = Overview
        fields = ()


class PerPrioritizationFilter(filters.FilterSet):
    overview = filters.NumberFilter(field_name="overview_id", lookup_expr="exact")

    class Meta:
        model = FormPrioritization
        fields = ()


class PerWorkPlanFilter(filters.FilterSet):
    overview = filters.NumberFilter(field_name="overview_id", lookup_expr="exact")

    class Meta:
        model = PerWorkPlan
        fields = ()


class FormAssessmentFilterSet(filters.FilterSet):
    overview = filters.NumberFilter(field_name="overview_id", lookup_expr="exact")

    class Meta:
        model = Form
        fields = ()
