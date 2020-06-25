from collections import defaultdict
from rest_framework.authentication import (
    TokenAuthentication,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django.db.models import Q, Sum, Count, F, Subquery, OuterRef, IntegerField
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from reversion.views import RevisionMixin

from .filters import ProjectFilter
from .models import (
    ERUOwner,
    ERU,
    PersonnelDeployment,
    Personnel,
    PartnerSocietyDeployment,
    Sectors,
    Statuses,
    RegionalProject,
    Project,
)
from api.models import Country, Region
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
    # Some figures are shown on the home page also, and not only authenticated users should see them.
    # permission_classes = (IsAuthenticated,)
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


class ProjectViewset(RevisionMixin, viewsets.ModelViewSet):
    queryset = Project.objects.prefetch_related(
        'user', 'reporting_ns', 'project_districts', 'event', 'dtype', 'regional_project',
    ).all()
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
        return Project.get_for(self.request.user, queryset=qs)


class RegionProjectViewset(viewsets.ViewSet):
    def get_region(self):
        if not hasattr(self, '_region'):
            self._region = get_object_or_404(Region, pk=self.kwargs['pk'])
        return self._region

    def get_projects(self):
        if self.action == 'global_national_society_activities':
            # Region Filter will be applied using ProjectFilter if provided
            qs = Project.objects.all()
        else:
            region = self.get_region()
            # Filter by region (From URL Params)
            qs = Project.objects.filter(
                Q(project_country__region=region) |
                Q(project_districts__country__region=region)
            ).distinct()
        # Filter by GET params
        qs = ProjectFilter(self.request.query_params, queryset=qs).qs
        # Filter by visibility
        return Project.get_for(self.request.user, queryset=qs)

    @action(detail=True, url_path='overview', methods=('get',))
    def overview(self, request, pk=None):
        projects = self.get_projects()
        aggregate_data = projects.aggregate(
            total_budget=Sum('budget_amount'),
            target_total=Sum('target_total'),
            reached_total=Sum('reached_total'),
        )
        return Response({
            'total_projects': projects.count(),
            'ns_with_ongoing_activities': projects.filter(
                status=Statuses.ONGOING).order_by('reporting_ns').values('reporting_ns').distinct().count(),
            'total_budget': aggregate_data['total_budget'],
            'target_total': aggregate_data['target_total'],
            'reached_total': aggregate_data['reached_total'],
            'projects_by_status': projects.order_by().values('status').annotate(
                count=Count('id', distinct=True)).values('status', 'count'),
        })

    @action(detail=True, url_path='movement-activities', methods=('get',))
    def movement_activities(self, request, pk=None):
        projects = self.get_projects()

        def _get_country_ns_sector_count():
            agg = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))
            fields = ('project_country', 'reporting_ns', 'primary_sector')
            qs = projects.order_by().values(*fields).annotate(count=Count('id', distinct=True)).values_list(
                *fields, 'project_country__name', 'reporting_ns__name', 'count')
            for country, ns, sector, country_name, ns_name, count in qs:
                agg[country][ns][sector] = count
                agg[country]['name'] = country_name
                agg[country][ns]['name'] = ns_name
            return [
                {
                    'id': cid,
                    'name': country.pop('name'),
                    'reporting_national_societies': [
                        {
                            'id': nsid,
                            'name': ns.pop('name'),
                            'sectors': [
                                {
                                    'id': sector,
                                    'sector': Sectors(sector).label,
                                    'count': count,
                                } for sector, count in ns.items()
                            ],
                        }
                        for nsid, ns in country.items()
                    ],
                }
                for cid, country in agg.items()
            ]

        region = self.get_region()
        country_projects = projects.filter(project_country=OuterRef('pk'))
        countries = Country.objects.filter(region=region)
        country_annotate = {
            f'{status_label.lower()}_projects_count': Coalesce(Subquery(
                country_projects.filter(status=status).values('project_country').annotate(
                    count=Count('id', distinct=True)).values('count')[:1],
                output_field=IntegerField(),
            ), 0) for status, status_label in Statuses.choices()
        }

        return Response({
            'total_projects': projects.count(),
            'countries_count': countries.annotate(
                projects_count=Coalesce(Subquery(
                    projects.filter(project_country=OuterRef('pk')).values('project_country').annotate(
                        count=Count('id', distinct=True)).values('count')[:1],
                    output_field=IntegerField(),
                ), 0),
                **country_annotate,
            ).values('id', 'name', 'iso', 'iso3', 'projects_count', *country_annotate.keys()),
            'country_ns_sector_count': _get_country_ns_sector_count(),
            'supporting_ns': projects.order_by().values('reporting_ns').annotate(count=Count('id', distinct=True)).values(
                'count', id=F('reporting_ns'), name=F('reporting_ns__name')),
        })

    @action(detail=True, url_path='national-society-activities', methods=('get',))
    def national_society_activities(self, request, pk=None):
        projects = self.get_projects()

        def _get_distinct(field, *args, **kwargs):
            return list(
                projects.order_by().values(field).annotate(
                    count=Count('id', distinct=True)).values(field, *args, **kwargs).distinct()
            )

        def _get_count(*fields):
            return list(
                projects.order_by().values(*fields).annotate(
                    count=Count('id', distinct=True)).values_list(*fields, 'count')
            )

        # Raw nodes
        supporting_ns_list = _get_distinct(
            'reporting_ns',
            iso3=F('reporting_ns__iso3'),
            iso=F('reporting_ns__iso'),
            name=F('reporting_ns__society_name')
        )
        receiving_ns_list = _get_distinct(
            'project_country',
            iso3=F('project_country__iso3'),
            iso=F('project_country__iso'),
            name=F('project_country__name')
        )
        sector_list = _get_distinct('primary_sector')

        # Raw links
        supporting_ns_and_sector_group = _get_count('reporting_ns', 'primary_sector')
        sector_and_receiving_ns_group = _get_count('primary_sector', 'project_country')

        # Node Types
        SUPPORTING_NS = 'supporting_ns'
        RECEIVING_NS = 'receiving_ns'
        SECTOR = 'sector'

        nodes = [
            {
                'id': node[id_selector],
                'type': gtype,
                **(
                    {
                        'name': node['name'],
                        'iso': node['iso'],
                        'iso3': node['iso3'],
                    } if gtype != SECTOR else {
                        'name': Sectors(node[id_selector]).label,
                    }
                )
            }
            for group, gtype, id_selector in [
                (supporting_ns_list, SUPPORTING_NS, 'reporting_ns'),
                (sector_list, SECTOR, 'primary_sector'),
                (receiving_ns_list, RECEIVING_NS, 'project_country'),
            ]
            for node in group
        ]

        node_id_map = {
            f"{node['type']}-{node['id']}": index
            for index, node in enumerate(nodes)
        }

        links = [
            {
                'source': node_id_map[f"{source_type}-{source}"],
                'target': node_id_map[f"{target_type}-{target}"],
                'value': value,
            }
            for group, source_type, target_type in [
                (supporting_ns_and_sector_group, SUPPORTING_NS, SECTOR),
                (sector_and_receiving_ns_group, SECTOR, RECEIVING_NS),
            ]
            for source, target, value in group
        ]
        return Response({'nodes': nodes, 'links': links})

    @action(detail=False, url_path='national-society-activities', methods=('get',))
    def global_national_society_activities(self, request, pk=None):
        return self.national_society_activities(request, pk)
