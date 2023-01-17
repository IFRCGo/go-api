from rest_framework.generics import (
    ListAPIView, RetrieveAPIView
)
from django_filters import rest_framework as filters

from .models import LocalUnit
from .serializers import LocalUnitSerializer


class LocalUnitFilters(filters.FilterSet):
    class Meta:
        model = LocalUnit
        fields = ('country', 'country__name')


class LocalUnitListAPIView(ListAPIView):
    queryset = LocalUnit.objects.all()
    serializer_class = LocalUnitSerializer
    filterset_class = LocalUnitFilters
    search_fields = ('name',)


class LocalUnitDetailAPIView(RetrieveAPIView):
    queryset = LocalUnit.objects.all()
    serializer_class = LocalUnitSerializer
