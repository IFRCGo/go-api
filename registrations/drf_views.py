from rest_framework import viewsets
from .models import DomainWhitelist
from .serializers import DomainWhitelistSerializer


class DomainWhitelistViewset(viewsets.ReadOnlyModelViewSet):
    queryset = DomainWhitelist.objects.all()
    serializer_class = DomainWhitelistSerializer
