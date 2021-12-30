from django_filters import rest_framework as filters
from .models import InformalUpdate


class InformalUpdateFilter(filters.FilterSet):
    hazayd_type = filters.NumberFilter(field_name='hazard_type', lookup_expr='exact')

    class Meta:
        model = InformalUpdate
        fields = {
            'created_at': ('exact', 'gt', 'gte', 'lt', 'lte'),
        }
