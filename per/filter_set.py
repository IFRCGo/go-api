import django_filters as filters

from api.models import Country
from per.models import (
    Form,
    FormPrioritization,
    OpsLearningCacheResponse,
    OpsLearningComponentCacheResponse,
    OpsLearningSectorCacheResponse,
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


class OpsLearningSummaryFilter(filters.FilterSet):
    sector = filters.ModelMultipleChoiceFilter(
        field_name="ops_learning_sector",
        queryset=OpsLearningSectorCacheResponse.objects.all(),
        help_text="Sector identifiers, comma separated",
    )

    per_component_validated__in = filters.ModelMultipleChoiceFilter(
        label="Component identifiers",
        field_name="ops_learning_component",
        help_text="PER Component identifiers, comma separated",
        queryset=OpsLearningComponentCacheResponse.objects.all(),
    )

    class Meta:
        model = OpsLearningCacheResponse
        fields = ()
