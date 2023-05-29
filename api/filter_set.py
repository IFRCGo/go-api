import django_filters as filters

from django.contrib.auth.models import User


class UserFilterSet(filters.FilterSet):
    name = filters.CharFilter(field_name='username', lookup_expr='icontains')
    email = filters.CharFilter(field_name='email', lookup_expr='icontains')

    class Meta:
        model = User
        fields = ()
