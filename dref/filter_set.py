import django_filters as filters

from dref.models import Dref


class DrefFilter(filters.FilterSet):
    status = filters.MultipleChoiceFilter(
        choices=Dref.Status.choices(),
        widget=filters.widgets.CSVWidget,
    )

    class Meta:
        model = Dref
        fields = ()
