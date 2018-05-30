from rest_framework import viewsets
from .models import (
    ERUOwner,
)
from .serializers import ERUOwnerSerializer

class ERUOwnerViewset(viewsets.ModelViewSet):
    queryset = ERUOwner.objects.all()
    serializer_class = ERUOwnerSerializer
