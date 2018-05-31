from rest_framework import viewsets
from .models import SurgeAlert, Subscription
from .serializers import SurgeAlertSerializer, SubscriptionSerializer

class SurgeAlertViewset(viewsets.ReadOnlyModelViewSet):
    queryset = SurgeAlert.objects.all()
    serializer_class = SurgeAlertSerializer

class SubscriptionViewset(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
