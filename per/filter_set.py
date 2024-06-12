import django_filters as filters

from api.models import Country
from per.models import (
    Form,
    FormPrioritization,
    Overview,
    PerDocumentUpload,
    PerWorkPlan,
)


class PerOverviewFilter(filters.FilterSet):
    country = filters.ModelMultipleChoiceFilter(field_name="country", queryset=Country.objects.all())
    region = filters.NumberFilter(field_name="country__region")
    id = filters.NumberFilter(field_name="id")

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


class PerDocumentFilter(filters.FilterSet):
    country = filters.NumberFilter(field_name="country")
    region = filters.NumberFilter(field_name="country__region")
    per = filters.NumberFilter(field_name="per")

    class Meta:
        model = PerDocumentUpload
        fields = ()
