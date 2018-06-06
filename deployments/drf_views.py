from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
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
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = ERUOwner.objects.all()
    serializer_class = ERUOwnerSerializer

class ERUViewset(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = ERU.objects.all()
    serializer_class = ERUSerializer

class HeopViewset(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Heop.objects.all()
    serializer_class = HeopSerializer

class FactViewset(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Fact.objects.all()
    serializer_class = FactSerializer

class RdrtViewset(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Rdrt.objects.all()
    serializer_class = RdrtSerializer

class FactPersonViewset(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = FactPerson.objects.all()
    serializer_class = FactPersonSerializer

class RdrtPersonViewset(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = RdrtPerson.objects.all()
    serializer_class = RdrtPersonSerializer
