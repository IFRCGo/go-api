from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, mixins

from .models import CountryOverview, FDRSIncome
from .serializers import CountryOverviewSerializer, FDRSIncomeSerializer
from .filter_set import FDRSIncomeFilter


class CountryOverviewViewSet(
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = CountryOverview.objects.all()
    # TODO: Use global authentication class
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    permission_classes = (IsAuthenticated,)
    serializer_class = CountryOverviewSerializer
    lookup_field = 'country__iso__iexact'


class FDRSIncomeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FDRSIncomeSerializer
    filterset_class = FDRSIncomeFilter

    def get_queryset(self):
        return FDRSIncome.objects.select_related('overview')