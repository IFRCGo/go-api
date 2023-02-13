import django_filters as filters

from dref.models import Dref, DrefOperationalUpdate
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
