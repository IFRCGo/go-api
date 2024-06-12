import django_filters as filters

from databank.models import FDRSIncome


class FDRSIncomeFilter(filters.FilterSet):
    country = filters.NumberFilter(field_name="overview__country")
    date__lte = filters.DateFilter(
        field_name="date",
        lookup_expr="lte",
    )
    date__gte = filters.DateFilter(
        field_name="date",
        lookup_expr="gte",
    )

    class Meta:
        model = FDRSIncome
        fields = ()
