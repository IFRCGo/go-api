from django.db.models import Q
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django_filters import Filter, rest_framework as filters
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
from api.models import Country
from .serializers import (
    ERUOwnerSerializer,
    ERUSerializer,
    HeopSerializer,
    FactSerializer,
    RdrtSerializer,
    FactPersonSerializer,
    RdrtPersonSerializer,
)

# https://github.com/carltongibson/django-filter/issues/137#issuecomment-127073878
class ListFilter(Filter):
    def __init__(self, filter_value=lambda x: x, **kwargs):
        super(ListFilter, self).__init__(**kwargs)
        self.filter_value_fn = filter_value

    def sanitize(self, value_list):
        return [v for v in value_list if v != u'']

    def filter(self, qs, value):
        values = value.split(u",")
        values = self.sanitize(values)
        values = map(self.filter_value_fn, values)
        f = Q()
        for v in values:
            kwargs = {self.name: v}
            f = f|Q(**kwargs)
        return qs.filter(f)

class ERUOwnerViewset(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = ERUOwner.objects.all()
    serializer_class = ERUOwnerSerializer
    ordering_fields = ('created_at', 'updated_at',)

class ERUFilter(filters.FilterSet):
    deployed_to__isnull = filters.BooleanFilter(name='deployed_to', lookup_expr='isnull')
    deployed_to__in = ListFilter(name='deployed_to__id')
    class Meta:
        model = ERU
        fields = ('available',)

class ERUViewset(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = ERU.objects.all()
    serializer_class = ERUSerializer
    filter_class = ERUFilter

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
