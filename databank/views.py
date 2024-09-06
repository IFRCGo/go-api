from rest_framework import mixins, viewsets
from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from main.permissions import DenyGuestUserPermission

from .filter_set import FDRSIncomeFilter
from .models import CountryOverview, FDRSIncome
from .serializers import CountryOverviewSerializer, FDRSIncomeSerializer


class CountryOverviewViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = CountryOverview.objects.all()
    # TODO: Use global authentication class
    authentication_classes = (BasicAuthentication, TokenAuthentication)
    permission_classes = (IsAuthenticated, DenyGuestUserPermission)
    serializer_class = CountryOverviewSerializer
    lookup_field = "country__iso__iexact"


class FDRSIncomeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FDRSIncomeSerializer
    filterset_class = FDRSIncomeFilter

    def get_queryset(self):
        return FDRSIncome.objects.select_related("overview", "indicator")
