from django_filters import rest_framework as filters
from .models import FlashUpdate


class FlashUpdateFilter(filters.FilterSet):
    hazard_type = filters.NumberFilter(field_name='hazard_type', lookup_expr='exact')

    class Meta:
        model = FlashUpdate
        fields = {
            'created_at': ('exact', 'gt', 'gte', 'lt', 'lte'),
        }
