from django_filters import rest_framework as filters

class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    pass
