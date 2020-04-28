import json, datetime, pytz
from rest_framework.authentication import (
    TokenAuthentication,
    BasicAuthentication,
    SessionAuthentication,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django_filters import rest_framework as filters
from django.shortcuts import render
from django.db.models import Q
from django.http import JsonResponse
from rest_framework import viewsets
from reversion.views import RevisionMixin

from .models import (
    ERUOwner,
    ERU,
    PersonnelDeployment,
    Personnel,
    PartnerSocietyDeployment,
    ProgrammeTypes,
    Sectors,
    OperationTypes,
    Statuses,
    RegionalProject,
    Project,
)
from api.models import Country
from api.view_filters import ListFilter
from .serializers import (
    ERUOwnerSerializer,
    ERUSerializer,
    PersonnelDeploymentSerializer,
    PersonnelSerializer,
    PartnerDeploymentSerializer,
    RegionalProjectSerializer,
    ProjectSerializer,
)
from api.views import (
    bad_request,
    bad_http_request,
    PublicJsonPostView,
    PublicJsonRequestView,
)


class ERUOwnerViewset(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = ERUOwner.objects.all()
    serializer_class = ERUOwnerSerializer
    ordering_fields = ('created_at', 'updated_at',)

class ERUFilter(filters.FilterSet):
    deployed_to__isnull = filters.BooleanFilter(field_name='deployed_to', lookup_expr='isnull')
    deployed_to__in = ListFilter(field_name='deployed_to__id')
    type = filters.NumberFilter(field_name='type', lookup_expr='exact')
    event = filters.NumberFilter(field_name='event', lookup_expr='exact')
    event__in = ListFilter(field_name='event')
    class Meta:
        model = ERU
        fields = ('available',)

class ERUViewset(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication,)
    #permission_classes = (IsAuthenticated,) # Some figures are shown on the home page also, and not only authenticated users should see them.
    queryset = ERU.objects.all()
    serializer_class = ERUSerializer
    filter_class = ERUFilter
    ordering_fields = ('type', 'units', 'equipment_units', 'deployed_to', 'event', 'eru_owner', 'available',)

class PersonnelDeploymentFilter(filters.FilterSet):
    country_deployed_to = filters.NumberFilter(field_name='country_deployed_to', lookup_expr='exact')
    region_deployed_to = filters.NumberFilter(field_name='region_deployed_to', lookup_expr='exact')
    event_deployed_to = filters.NumberFilter(field_name='event_deployed_to', lookup_expr='exact')
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
    country_from = filters.NumberFilter(field_name='country_from', lookup_expr='exact')
    type = filters.CharFilter(field_name='type', lookup_expr='exact')
    event_deployed_to = filters.NumberFilter(field_name='deployment__event_deployed_to', lookup_expr='exact')
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
    parent_society = filters.NumberFilter(field_name='parent_society', lookup_expr='exact')
    country_deployed_to = filters.NumberFilter(field_name='country_deployed_to', lookup_expr='exact')
    district_deployed_to = filters.NumberFilter(field_name='district_deployed_to', lookup_expr='exact')
    parent_society__in = ListFilter(field_name='parent_society__id')
    country_deployed_to__in = ListFilter(field_name='country_deployed_to__id')
    district_deployed_to__in = ListFilter(field_name='district_deployed_to__id')
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


class RegionalProjectViewset(viewsets.ReadOnlyModelViewSet):
    queryset = RegionalProject.objects.all()
    serializer_class = RegionalProjectSerializer
    search_fields = ('name',)


class ProjectFilter(filters.FilterSet):
    budget_amount = filters.NumberFilter(field_name='budget_amount', lookup_expr='exact')
    country = filters.CharFilter(field_name='country', method='filter_country')

    def filter_country(self, queryset, name, value):
        return queryset.filter(
            # ISO2
            Q(project_country__iso__iexact=value) |
            Q(project_district__country__iso__iexact=value) |
            # ISO3
            Q(project_country__iso3__iexact=value) |
            Q(project_district__country__iso3__iexact=value)
        )

    class Meta:
        model = Project
        fields = [
            'country',
            'budget_amount',
            'start_date',
            'end_date',
            'project_district',
            'reporting_ns',
            'programme_type',
            'status',
            'primary_sector',
            'operation_type',
        ]


class ProjectViewset(RevisionMixin, viewsets.ModelViewSet):
    queryset = Project.objects.prefetch_related(
        'user', 'reporting_ns', 'project_district', 'event', 'dtype', 'regional_project',
    ).all()
    # XXX: Use this as default authentication classes
    authentication_classes = (
        TokenAuthentication,
        BasicAuthentication,
        SessionAuthentication,
    )
    # TODO: May require different permission for UNSAFE_METHODS (Also Country Level)
    filter_class = ProjectFilter
    serializer_class = ProjectSerializer
    ordering_fields = ('name',)

    def get_permissions(self):
        # Require authentication for unsafe methods only
        if self.action in ['list', 'retrieve']:
            permission_classes = []
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        # Public Project are viewable to unauthenticated or non-ifrc users
        qs = super().get_queryset()
        user = self.request.user
        if user.is_authenticated:
            if user.email and user.email.endswith('@ifrc.org'):
                return qs
            return qs.exclude(visibility=Project.IFRC_ONLY)
        return qs.filter(visibility=Project.PUBLIC)
