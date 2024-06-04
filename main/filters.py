from django.db.models import F, OrderBy
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    pass


class NullsLastOrderingFilter(OrderingFilter):
    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)

        if ordering:
            nulls_last_ordering = []
            for field in ordering:
                if field.startswith("-"):
                    nulls_last_ordering.append(F(field[1:]).desc(nulls_last=True))
                else:
                    nulls_last_ordering.append(F(field).asc(nulls_last=True))

            return nulls_last_ordering

        return ordering
