from rest_framework.authentication import TokenAuthentication
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
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
