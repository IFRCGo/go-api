import django_filters as filters

from dref.models import Dref
from api.models import Country


class DrefFilter(filters.FilterSet):
    status = filters.MultipleChoiceFilter(
        choices=Dref.Status.choices,
        lookup_expr='in',
        widget=filters.widgets.CSVWidget,
    )
    country = filters.ModelMultipleChoiceFilter(
        field_name='drefcountrydistrict__country',
        queryset=Country.objects.all()
    )

    class Meta:
        model = Dref
        fields = ['is_published']
