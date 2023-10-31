from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, mixins

from .models import CountryOverview
from .serializers import CountryOverviewSerializer


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
