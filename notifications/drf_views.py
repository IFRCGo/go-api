from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from .models import SurgeAlert, Subscription
from .serializers import (
    SurgeAlertSerializer,
    UnauthenticatedSurgeAlertSerializer,
    SubscriptionSerializer,
)

class SurgeAlertViewset(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication,)
    queryset = SurgeAlert.objects.all()
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
