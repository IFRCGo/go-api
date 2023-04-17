import django_filters as filters

from per.models import Overview
from api.models import Country


class PerOverviewFilter(filters.FilterSet):
    country = filters.ModelMultipleChoiceFilter(field_name="country", queryset=Country.objects.all())

    class Meta:
        model = Overview
        fields = ()
