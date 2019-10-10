import json, datetime, pytz
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework as filters
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import viewsets
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
    deployed_to__isnull = filters.BooleanFilter(name='deployed_to', lookup_expr='isnull')
    deployed_to__in = ListFilter(name='deployed_to__id')
    type = filters.NumberFilter(name='type', lookup_expr='exact')
    event = filters.NumberFilter(name='event', lookup_expr='exact')
    event__in = ListFilter(name='event')
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


class ProjectFilter(filters.FilterSet):
    budget_amount = filters.NumberFilter(name='budget_amount', lookup_expr='exact')
    country = filters.CharFilter(name='country', method='filter_country')

    def filter_country(self, queryset, name, value):
        return queryset.filter(project_district__country__iso=value)

    class Meta:
        model = Project
        fields = [
            'country',
            'budget_amount',
            'start_date',
            'end_date',
            'project_district__country',
            'reporting_ns',
            'programme_type',
            'status',
            'primary_sector',
            'operation_type',
        ]


class ProjectViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Project.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    filter_class = ProjectFilter
    serializer_class = ProjectSerializer
    ordering_fields = ('name',)


class CreateProject(PublicJsonPostView):
    def handle_post(self, request, *args, **kwargs):
        body = json.loads(request.body.decode('utf-8'))
        # Recently it is not checked whether what user is this (same with the logged in or not).
        required_fields = [
            'user',
            'reporting_ns',
            'project_district',
            'name',
        ]
        missing_fields = [field for field in required_fields if field not in body]
        if len(missing_fields):
            return bad_request('Could not complete request due to missing mandatory field. Please submit %s' % ', '.join(missing_fields))

        currentDT = datetime.datetime.now(pytz.timezone('UTC'))
        if 'programme_type' not in body:
            body['programme_type'] = ProgrammeTypes.MULTILATERAL
        if 'primary_sector' not in body:
            body['primary_sector'] = Sectors.WASH
        if 'secondary_sectors' not in body:
            body['secondary_sectors'] = []
        if 'operation_type' not in body:
            body['operation_type'] = OperationTypes.LONG_TERM_OPERATION
        if 'start_date' not in body:
            body['start_date'] = str(currentDT)
        if 'end_date' not in body:
            body['end_date'] = str(currentDT)
        if 'budget_amount' not in body:
            body['budget_amount'] = 0
        if 'status' not in body:
            body['status'] = Statuses.ONGOING
        project = Project.objects.create(user_id             = body['user'],
                                         reporting_ns_id     = body['reporting_ns'],
                                         project_district_id = body['project_district'],
                                         name                = body['name'],
                                         programme_type      = body['programme_type'],
                                         primary_sector      = body['primary_sector'],
                                         secondary_sectors   = body['secondary_sectors'],
                                         operation_type      = body['operation_type'],
                                         start_date          = body['start_date'],
                                         end_date            = body['end_date'],
                                         budget_amount       = body['budget_amount'],
                                         status              = body['status'],
                                         )
        try:
            project.save()
        except:
            return bad_request('Could not create Project record.')
        return JsonResponse({'status': 'ok'})
