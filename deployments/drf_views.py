from collections import defaultdict
import datetime
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from django_filters import rest_framework as filters
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.functions import Coalesce, Cast
from django.contrib.postgres.aggregates.general import ArrayAgg
from django.shortcuts import get_object_or_404
from reversion.views import RevisionMixin
from main.utils import is_tableau

from main.serializers import CsvListMixin
from api.models import (
    Country,
    Region,
    FieldReport,
)
from api.view_filters import ListFilter
from api.visibility_class import ReadOnlyVisibilityViewsetMixin

from .filters import ProjectFilter
from .utils import get_previous_months
from .models import (
    ERU,
    ERUOwner,
    OperationTypes,
    PartnerSocietyDeployment,
    Personnel,
    PersonnelDeployment,
    ProgrammeTypes,
    Project,
    RegionalProject,
    SectorTags,
    Sectors,
    Statuses,
)
from .serializers import (
    ERUOwnerSerializer,
    ERUSerializer,
    PersonnelDeploymentSerializer,
    PersonnelSerializer,
    PersonnelCsvSerializer,
    PartnerDeploymentSerializer,
    PartnerDeploymentTableauSerializer,
    RegionalProjectSerializer,
    ProjectSerializer,
    ProjectCsvSerializer,
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
    filterset_class = ERUFilter
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
    filterset_class = PersonnelDeploymentFilter
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
    filterset_class = PersonnelFilter
    ordering_fields = ('start_date', 'end_date', 'name', 'role', 'type', 'country_from', 'deployment',)

    def get_queryset(self):
        qs = super().get_queryset().filter(is_active=True).select_related(
            'country_from',
            'deployment__country_deployed_to',
            'deployment__event_deployed_to',
            'deployment__event_deployed_to__dtype'
        ).prefetch_related(
            'deployment__event_deployed_to__countries',
            'deployment__event_deployed_to__appeals',
        )

        if self.request.GET.get('format') == 'csv':
            return qs.prefetch_related(
                models.Prefetch(
                    'deployment__event_deployed_to__field_reports',
                    queryset=FieldReport.objects.only('id', 'event_id')
                )
            )
        return qs.prefetch_related('deployment__event_deployed_to__field_reports')

    def get_serializer_class(self):
        request_format_type = self.request.GET.get('format', 'json')
        if request_format_type == 'csv':
            return PersonnelCsvSerializer
        return PersonnelSerializer


class AggregateDeployments(APIView):
    '''
        Get aggregated data for personnel deployments
    '''
    def get(self, request):
        now = datetime.datetime.now()
        deployments_qset = Personnel.objects.filter(is_active=True)
        eru_qset = ERU.objects.all()
        if request.GET.get('event'):
            event_id = request.GET.get('event')
            deployments_qset = deployments_qset.filter(personneldeployment__event_deployed_to=event_id)
            eru_qset = eru_qset.filter(event=event_id)
        active_deployments = deployments_qset.filter(
            start_date__lt=now,
            end_date__gt=now
        ).count()
        active_erus = eru_qset.filter(
            start_date__lt=now,
            end_date__gt=now
        ).count()
        deployments_this_year = deployments_qset.filter(
            is_active=True,
            start_date__year__lte=now.year,
            end_date__year__gte=now.year
        ).count()
        return Response({
            'active_deployments': active_deployments,
            'active_erus': active_erus,
            'deployments_this_year': deployments_this_year 
        })

class DeploymentsByMonth(APIView):
    
    def get(self, request):
        '''Returns count of Personnel Deployments
            for last 12 months, aggregated by month.
        '''
        now = datetime.datetime.now()
        months = get_previous_months(now, 12)
        deployment_counts = {}
        for month in months:
            month_string = month[0]
            first_day = month[1]
            last_day = month[2]
            count = Personnel.objects.filter(
                start_date__date__lte=last_day,
                end_date__date__gte=first_day
            ).count()
            deployment_counts[month_string] = count
        return Response(deployment_counts)            



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
    filterset_class = PartnerDeploymentFilterset

    def get_serializer_class(self):
        if is_tableau(self.request) is True:
            return PartnerDeploymentTableauSerializer
        return PartnerDeploymentSerializer


class RegionalProjectViewset(viewsets.ReadOnlyModelViewSet):
    queryset = RegionalProject.objects.all()
    serializer_class = RegionalProjectSerializer
    search_fields = ('name',)


class ProjectViewset(
    RevisionMixin,
    CsvListMixin,
    ReadOnlyVisibilityViewsetMixin,
    viewsets.ModelViewSet,
):
    queryset = Project.objects.prefetch_related(
        'user', 'reporting_ns', 'project_districts', 'event', 'dtype', 'regional_project',
    ).all()
    filterset_class = ProjectFilter
    serializer_class = ProjectSerializer
    csv_serializer_class = ProjectCsvSerializer
    ordering_fields = ('name',)

    def get_permissions(self):
        # Require authentication for unsafe methods only
        if self.action in ['list', 'retrieve']:
            permission_classes = []
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class RegionProjectViewset(ReadOnlyVisibilityViewsetMixin, viewsets.ViewSet):
    def get_region(self):
        if not hasattr(self, '_region'):
            self._region = get_object_or_404(Region, pk=self.kwargs['pk'])
        return self._region

    def get_projects(self):
        # Region Filter will be applied using ProjectFilter if provided
        # Filter by visibility
        qs = self.get_visibility_queryset(Project.objects.all())
        if self.action != 'global_national_society_activities':
            region = self.get_region()
            # Filter by region (From URL Params)
            qs = qs.filter(
                models.Q(project_country__region=region) |
                models.Q(project_districts__country__region=region)
            ).distinct()
        # Filter by GET params
        return ProjectFilter(self.request.query_params, queryset=qs).qs

    @action(detail=True, url_path='overview', methods=('get',))
    def overview(self, request, pk=None):
        projects = self.get_projects()
        aggregate_data = projects.aggregate(
            total_budget=models.Sum('budget_amount'),
            target_total=models.Sum('target_total'),
            reached_total=models.Sum('reached_total'),
        )
        return Response({
            'total_projects': projects.count(),
            'ns_with_ongoing_activities': projects.filter(
                status=Statuses.ONGOING).order_by('reporting_ns').values('reporting_ns').distinct().count(),
            'total_budget': aggregate_data['total_budget'],
            'target_total': aggregate_data['target_total'],
            'reached_total': aggregate_data['reached_total'],
            'projects_by_status': projects.order_by().values('status').annotate(
                count=models.Count('id', distinct=True)).values('status', 'count'),
        })

    @action(detail=True, url_path='movement-activities', methods=('get',))
    def movement_activities(self, request, pk=None):
        projects = self.get_projects()

        def _get_country_ns_sector_count():
            agg = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))
            fields = ('project_country', 'reporting_ns', 'primary_sector')
            qs = projects.order_by().values(*fields).annotate(count=models.Count('id', distinct=True)).values_list(
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
        country_projects = projects.filter(project_country=models.OuterRef('pk'))
        countries = Country.objects.filter(region=region)
        country_annotate = {
            f'{status_label.lower()}_projects_count': Coalesce(models.Subquery(
                country_projects.filter(status=status).values('project_country').annotate(
                    count=models.Count('id', distinct=True)).values('count')[:1],
                output_field=models.IntegerField(),
            ), 0) for status, status_label in Statuses.choices()
        }

        return Response({
            'total_projects': projects.count(),
            'countries_count': countries.annotate(
                projects_count=Coalesce(models.Subquery(
                    projects.filter(project_country=models.OuterRef('pk')).values('project_country').annotate(
                        count=models.Count('id', distinct=True)).values('count')[:1],
                    output_field=models.IntegerField(),
                ), 0),
                **country_annotate,
            ).values('id', 'name', 'iso', 'iso3', 'projects_count', *country_annotate.keys()),
            'country_ns_sector_count': _get_country_ns_sector_count(),
            'supporting_ns': [
                {'id': id, 'name': name, 'count': count}
                for id, name, count in projects.order_by().values('reporting_ns').annotate(
                    count=models.Count('id', distinct=True)
                ).values_list('reporting_ns', 'reporting_ns__name', 'count')
            ],
        })

    @action(detail=True, url_path='national-society-activities', methods=('get',))
    def national_society_activities(self, request, pk=None):
        projects = self.get_projects()

        def _get_distinct(field, *args, **kwargs):
            kwargs[field] = field
            return [
                {
                    f: p[key]
                    for f, key in kwargs.items()
                }
                for p in projects.order_by().values(field).annotate(
                    count=models.Count('id', distinct=True)
                ).values(field, *kwargs.values()).distinct()
            ]

        def _get_count(*fields):
            return list(
                projects.order_by().values(*fields).annotate(
                    count=models.Count('id', distinct=True)).values_list(*fields, 'count')
            )

        # Raw nodes
        supporting_ns_list = _get_distinct(
            'reporting_ns',
            iso3='reporting_ns__iso3',
            iso='reporting_ns__iso',
            name='reporting_ns__society_name',
        )
        receiving_ns_list = _get_distinct(
            'project_country',
            iso3='project_country__iso3',
            iso='project_country__iso',
            name='project_country__name',
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


class GlobalProjectViewset(ReadOnlyVisibilityViewsetMixin, viewsets.ViewSet):
    def get_projects(self):
        # Filter by visibility
        qs = self.get_visibility_queryset(Project.objects.all())
        # Filter by GET params
        projects = ProjectFilter(self.request.query_params, queryset=qs).qs
        return Project.objects.filter(
            # To avoid duplicate rows
            id__in=projects,
            # NOTE: Only process ongoing projects in global project view
            status=Statuses.ONGOING,
        )

    @action(detail=False, url_path='overview', methods=('get',))
    def overview(self, request, pk=None):
        def _get_projects_per_enum_field(projects, EnumType, enum_field):
            return [
                {
                    enum_field: enum_field_value,
                    f'{enum_field}_display': EnumType(int(enum_field_value)).label,
                    'count': count,
                }
                for enum_field_value, count in (
                    projects.order_by().values(enum_field).annotate(count=models.Count('id')).values_list(
                        enum_field, 'count',
                    )
                )
            ]

        projects = self.get_projects()
        projects_unnest_tags = (
            projects
            # XXX: Without cast django throws 'int' is not iterable
            .annotate(secondary_sector=Cast(
                models.Func(models.F('secondary_sectors'), function='UNNEST'),
                output_field=models.CharField(),
            ))
        )

        target_total = projects.aggregate(target_total=models.Sum('target_total'))['target_total']
        return Response({
            'total_ongoing_projects': projects.filter(status=Statuses.ONGOING).count(),
            'ns_with_ongoing_activities': (
                projects.filter(status=Statuses.ONGOING)
                .order_by('reporting_ns').values('reporting_ns').distinct().count()
            ),
            'target_total': target_total,
            'projects_per_sector': _get_projects_per_enum_field(projects, Sectors, 'primary_sector'),
            'projects_per_programme_type': _get_projects_per_enum_field(projects, ProgrammeTypes, 'programme_type'),
            'projects_per_secondary_sectors': _get_projects_per_enum_field(
                projects_unnest_tags,
                SectorTags, 'secondary_sector'
            ),
        })

    @action(detail=False, url_path='ns-ongoing-projects-stats', methods=('get',))
    def ns_ongoing_projects_stats(self, request, pk=None):
        projects = self.get_projects()
        ref_projects = projects.filter(reporting_ns=models.OuterRef('pk'))

        project_per_sector = defaultdict(list)
        for reporting_ns, primary_sector, count in (
            projects.order_by('reporting_ns', 'primary_sector')
            .values('reporting_ns', 'primary_sector')
            .annotate(count=models.Count('id'))
            .values_list('reporting_ns', 'primary_sector', 'count')
        ):
            project_per_sector[reporting_ns].append({
                'primary_sector': primary_sector,
                'primary_sector_display': Sectors(primary_sector).label,
                'count': count,
            })

        return Response({
            'results': [
                {
                    **ns_data,
                    'projects_per_sector': project_per_sector.get(ns_data['id']),
                    'operation_types_display': [
                        OperationTypes(operation_type).label
                        for operation_type in ns_data['operation_types']
                    ]
                }
                for ns_data in Country.objects.annotate(
                    ongoing_projects=Coalesce(models.Subquery(
                        ref_projects.values('reporting_ns').annotate(
                            count=models.Count('id')).values('count')[:1],
                        output_field=models.IntegerField(),
                    ), 0),
                    target_total=Coalesce(models.Subquery(
                        ref_projects.values('reporting_ns').annotate(
                            target_total=models.Sum('target_total')).values('target_total')[:1],
                        output_field=models.IntegerField(),
                    ), 0),
                    budget_amount_total=Coalesce(models.Subquery(
                        ref_projects.values('reporting_ns').annotate(
                            budget_amount_total=models.Sum('budget_amount')).values('budget_amount_total')[:1],
                        output_field=models.IntegerField(),
                    ), 0),
                    operation_types=Coalesce(models.Subquery(
                        ref_projects.values('reporting_ns').annotate(
                            operation_types=ArrayAgg('operation_type', distinct=True)).values('operation_types')[:1],
                        output_field=ArrayField(models.IntegerField()),
                    ), []),
                ).filter(ongoing_projects__gt=0).order_by('id').values(
                    'id', 'name', 'iso3', 'iso3', 'society_name',
                    'ongoing_projects', 'target_total', 'budget_amount_total', 'operation_types',
                )
            ]
        })
