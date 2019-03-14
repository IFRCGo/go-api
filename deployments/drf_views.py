from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework as filters
from rest_framework import viewsets
from .models import (
    ERUOwner,
    ERU,
    PersonnelDeployment,
    Personnel,
    PartnerSocietyDeployment,
)
from api.models import Country
from api.view_filters import ListFilter
from .serializers import (
    ERUOwnerSerializer,
    ERUSerializer,
    PersonnelDeploymentSerializer,
    PersonnelSerializer,
    PartnerDeploymentSerializer,
)

class ERUOwnerViewset(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = ERUOwner.objects.all()
    serializer_class = ERUOwnerSerializer
    ordering_fields = ('created_at', 'updated_at',)

class ERUFilter(filters.FilterSet):
    deployed_to__isnull = filters.BooleanFilter(name='deployed_to', lookup_expr='isnull')
    deployed_to__in = ListFilter(name='deployed_to__id')
    type = filters.NumberFilter(name='type', lookup_expr='exact')
    event = filters.NumberFilter(name='event', lookup_expr='exact')
    class Meta:
        model = ERU
        fields = ('available',)

class ERUViewset(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = ERU.objects.all()
    serializer_class = ERUSerializer
    filter_class = ERUFilter
    ordering_fields = ('type', 'units', 'equipment_units', 'deployed_to', 'event', 'eru_owner', 'available',)

class PersonnelDeploymentFilter(filters.FilterSet):
    country_deployed_to = filters.NumberFilter(name='country_deployed_to', lookup_expr='exact')
    region_deployed_to = filters.NumberFilter(name='region_deployed_to', lookup_expr='exact')
    event_deployed_to = filters.NumberFilter(name='event_deployed_to', lookup_expr='exact')
    class Meta:
        model = PersonnelDeployment
        fields = ('country_deployed_to', 'region_deployed_to', 'event_deployed_to',)

class PersonnelDeploymentViewset(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = PersonnelDeployment.objects.all()
    serializer_class = PersonnelDeploymentSerializer
    filter_class = PersonnelDeploymentFilter
    ordering_fields = ('country_deployed_to', 'region_deployed_to', 'event_deployed_to',)

class PersonnelFilter(filters.FilterSet):
    country_from = filters.NumberFilter(name='country_from', lookup_expr='exact')
    type = filters.CharFilter(name='type', lookup_expr='exact')
    event_deployed_to = filters.NumberFilter(name='deployment__event_deployed_to', lookup_expr='exact')
    class Meta:
        model = Personnel
        fields = {
            'start_date': ('exact', 'gt', 'gte', 'lt', 'lte'),
            'end_date': ('exact', 'gt', 'gte', 'lt', 'lte')
        }

class PersonnelViewset(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Personnel.objects.all()
    serializer_class = PersonnelSerializer
    filter_class = PersonnelFilter
    ordering_fields = ('start_date', 'end_date', 'name', 'role', 'type', 'country_from', 'deployment',)

class PartnerDeploymentFilterset(filters.FilterSet):
    parent_society = filters.NumberFilter(name='parent_society', lookup_expr='exact')
    country_deployed_to = filters.NumberFilter(name='country_deployed_to', lookup_expr='exact')
    district_deployed_to = filters.NumberFilter(name='district_deployed_to', lookup_expr='exact')
    parent_society__in = ListFilter(name='parent_society__id')
    country_deployed_to__in = ListFilter(name='country_deployed_to__id')
    district_deployed_to__in = ListFilter(name='district_deployed_to__id')
    class Meta:
        model = PartnerSocietyDeployment
        fields = {
            'start_date': ('exact', 'gt', 'gte', 'lt', 'lte'),
            'end_date': ('exact', 'gt', 'gte', 'lt', 'lte'),
        }

class PartnerDeploymentViewset(viewsets.ReadOnlyModelViewSet):
    queryset = PartnerSocietyDeployment.objects.all()
    serializer_class = PartnerDeploymentSerializer
    filter_class = PartnerDeploymentFilterset
