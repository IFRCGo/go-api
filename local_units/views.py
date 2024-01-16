from rest_framework.generics import (
    ListAPIView, RetrieveAPIView
)
from django_filters import rest_framework as filters

from .models import LocalUnit, DelegationOffice
from .serializers import LocalUnitSerializer, DelegationOfficeSerializer


class LocalUnitFilters(filters.FilterSet):
    class Meta:
        model = LocalUnit
        fields = (
            'country__name',
            'country__iso3',
            'country__iso',
            'type__code',
            'draft',
            'validated',
        )


class LocalUnitListAPIView(ListAPIView):
    queryset = LocalUnit.objects.all()
    serializer_class = LocalUnitSerializer
    filterset_class = LocalUnitFilters
    search_fields = ('local_branch_name', 'english_branch_name',)


class LocalUnitDetailAPIView(RetrieveAPIView):
    queryset = LocalUnit.objects.all()
    serializer_class = LocalUnitSerializer


class DelegationOfficeFilters(filters.FilterSet):
    class Meta:
        model = DelegationOffice
        fields = (
            'country__name',
            'country__iso3',
            'country__iso',
            'dotype__code',
        )


class DelegationOfficeListAPIView(ListAPIView):
    queryset = DelegationOffice.objects.all()
    serializer_class = DelegationOfficeSerializer
    filterset_class = DelegationOfficeFilters
    search_fields = ('name', 'country__name')


class DelegationOfficeDetailAPIView(RetrieveAPIView):
    queryset = DelegationOffice.objects.all()
    serializer_class = DelegationOfficeSerializer
