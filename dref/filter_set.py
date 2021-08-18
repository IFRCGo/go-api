import django_filters as filters

from dref.models import Dref
from api.models import Country


class DrefFilter(filters.FilterSet):
    status = filters.MultipleChoiceFilter(
        choices=Dref.Status.choices(),
        widget=filters.widgets.CSVWidget,
    )
    national_society = filters.ModelMultipleChoiceFilter(
        queryset=Country.objects.all()
    )

    class Meta:
        model = Dref
        fields = ()
