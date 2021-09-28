from django_filters import rest_framework as filters
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from .models import SurgeAlert, Subscription
from .serializers import (
    SurgeAlertSerializer,
#   UnauthenticatedSurgeAlertSerializer,
    SubscriptionSerializer,
)


class SurgeAlertFilter(filters.FilterSet):
    atype = filters.NumberFilter(field_name='atype', lookup_expr='exact')
    category = filters.NumberFilter(field_name='category', lookup_expr='exact')
    event = filters.NumberFilter(field_name='event', lookup_expr='exact')

    class Meta:
        model = SurgeAlert
        fields = {
            'created_at': ('exact', 'gt', 'gte', 'lt', 'lte'),
            'is_active': ('exact',)
        }


class SurgeAlertViewset(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication,)
    queryset = SurgeAlert.objects.all()
    filterset_class = SurgeAlertFilter
    ordering_fields = ('molnix_status', 'created_at', 'atype', 'category', 'event',)
    # molnix status can be active (open) or unfilled (stood down) or none

    def get_serializer_class(self):
        # if self.request.user.is_authenticated:
        #     return SurgeAlertSerializer
        # return UnauthenticatedSurgeAlertSerializer
        return SurgeAlertSerializer

class SubscriptionViewset(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)
