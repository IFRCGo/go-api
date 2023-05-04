import django_filters as filters
from django.db import models

from dref.models import (
    Dref,
    DrefOperationalUpdate,
    DrefFinalReport,
)
from api.models import Country


class DrefFilter(filters.FilterSet):
    status = filters.MultipleChoiceFilter(
        choices=Dref.Status.choices,
        lookup_expr="in",
        widget=filters.widgets.CSVWidget,
    )
    country = filters.ModelMultipleChoiceFilter(field_name="country", queryset=Country.objects.all())

    class Meta:
        model = Dref
        fields = ["is_published"]


class DrefOperationalUpdateFilter(filters.FilterSet):
    dref = filters.ModelMultipleChoiceFilter(field_name="dref", queryset=Dref.objects.all().distinct())

    class Meta:
        model = DrefOperationalUpdate
        fields = ["is_published"]


class CompletedDrefOperationsFilterSet(filters.FilterSet):

    class Type(models.TextChoices):
        DREF = 'dref', 'Dref'
        OPERATIONAL_UPDATE = 'operational_update', 'Operational Update'
        FINAL_REPORT = 'final_report', 'Final Report'

    country = filters.ModelMultipleChoiceFilter(field_name="country", queryset=Country.objects.all())
    created_at__lte = filters.DateFilter(field_name="created_at", lookup_expr="lte", input_formats=["%Y-%m-%d"])
    created_at__gte = filters.DateFilter(field_name="created_at", lookup_expr="gte", input_formats=["%Y-%m-%d"])
    type_of_dref = filters.MultipleChoiceFilter(
        choices=Dref.DrefType.choices,
        lookup_expr="in",
        widget=filters.widgets.CSVWidget,
    )
    # type = filters.ChoiceFilter(
    #     label='Tyoe choice',
    #     choices=Type.choices,
    #     methods='filter_type'

    # )

    class Meta:
        model = DrefFinalReport
        fields = ()

    # def filter_type(self, qs, name, value):
    #     pass
