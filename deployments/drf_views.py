from rest_framework import viewsets
from .models import (
    ERUOwner,
    ERU,
    Heop,
    Fact,
    FactPerson,
    Rdrt,
    RdrtPerson,
)
from .serializers import (
    ERUOwnerSerializer,
    ERUSerializer,
    HeopSerializer,
    FactSerializer,
    RdrtSerializer,
    FactPersonSerializer,
    RdrtPersonSerializer,
)

class ERUOwnerViewset(viewsets.ReadOnlyModelViewSet):
    queryset = ERUOwner.objects.all()
    serializer_class = ERUOwnerSerializer

class ERUViewset(viewsets.ReadOnlyModelViewSet):
    queryset = ERU.objects.all()
    serializer_class = ERUSerializer

class HeopViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Heop.objects.all()
    serializer_class = HeopSerializer

class FactViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Fact.objects.all()
    serializer_class = FactSerializer

class RdrtViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Rdrt.objects.all()
    serializer_class = RdrtSerializer

class FactPersonViewset(viewsets.ReadOnlyModelViewSet):
    queryset = FactPerson.objects.all()
    serializer_class = FactPersonSerializer

class RdrtPersonViewset(viewsets.ReadOnlyModelViewSet):
    queryset = RdrtPerson.objects.all()
    serializer_class = RdrtPersonSerializer
