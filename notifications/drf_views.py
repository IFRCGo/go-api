from django_filters import rest_framework as filters
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from .models import SurgeAlert, Subscription
from .serializers import (
    SurgeAlertSerializer,
    UnauthenticatedSurgeAlertSerializer,
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
        }

class SurgeAlertViewset(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication,)
    queryset = SurgeAlert.objects.all()
    filter_class = SurgeAlertFilter
    ordering_fields = ('created_at', 'atype', 'category', 'event',)
    def get_serializer_class(self):
        if self.request.user.is_authenticated:
            return SurgeAlertSerializer
        return UnauthenticatedSurgeAlertSerializer

class SubscriptionViewset(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)
