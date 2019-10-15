from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK
from rest_framework.generics import GenericAPIView, CreateAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from django_filters import rest_framework as filters
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from .event_sources import SOURCES
from .exceptions import BadRequest
from .view_filters import ListFilter
from .visibility_class import ReadOnlyVisibilityViewset
from deployments.models import Personnel

from .models import (
    DisasterType,

    Region,
    RegionKeyFigure,
    RegionSnippet,

    Country,
    CountryKeyFigure,
    CountrySnippet,

    District,

    Snippet,
    Event,
    Snippet,
    SituationReport,
    SituationReportType,
    Appeal,
    AppealDocument,
    Profile,
    FieldReport,
    FieldReportContact,
    ActionsTaken,
    Source,
    SourceType,

    VisibilityChoices,
    RequestChoices,
)

from .serializers import (
    DisasterTypeSerializer,

    RegionSerializer,
    RegionKeyFigureSerializer,
    RegionSnippetSerializer,
    RegionRelationSerializer,

    CountrySerializer,
    CountryKeyFigureSerializer,
    CountrySnippetSerializer,
    CountryRelationSerializer,

    DistrictSerializer,
    MiniDistrictSerializer,

    SnippetSerializer,
    ListEventSerializer,
    ListEventDeploymentsSerializer,
    DetailEventSerializer,
    SituationReportSerializer,
    SituationReportTypeSerializer,
    AppealSerializer,
    AppealDocumentSerializer,
    UserSerializer,
    ProfileSerializer,
    ListFieldReportSerializer,
    DetailFieldReportSerializer,
    CreateFieldReportSerializer,
)
from .logger import logger


class EventDeploymentsViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = ListEventDeploymentsSerializer

    def get_queryset(self):
        return Personnel.objects.filter(
                end_date__gt=timezone.now(),
            ).order_by().values(
                'deployment__event_deployed_to', 'type',
            ).annotate(
                id=models.F('deployment__event_deployed_to'),
                deployments=models.Count('type')
            ).values('id', 'type', 'deployments')


class DisasterTypeViewset(viewsets.ReadOnlyModelViewSet):
    queryset = DisasterType.objects.all()
    serializer_class = DisasterTypeSerializer

class RegionViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Region.objects.all()
    def get_serializer_class(self):
        if self.action == 'list':
            return RegionSerializer
        return RegionRelationSerializer

class CountryFilter(filters.FilterSet):
    region = filters.NumberFilter(name='region', lookup_expr='exact')
    class Meta:
        model = Country
        fields = ('region',)

class CountryViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.all()
    filter_class = CountryFilter

    def get_object(self):
        pk = self.kwargs['pk']
        try:
            return Country.objects.get(pk=int(pk))
        except ValueError:
            # NOTE: If pk is not integer try searching for name or iso
            country = Country.objects.filter(
                models.Q(name__iexact=str(pk)) | models.Q(iso__iexact=str(pk))
            )
            if country.exists():
                return country.first()
            raise Country.DoesNotExist(
                'Country matching query does not exist.'
            )

    def get_serializer_class(self):
        if self.action == 'list':
            return CountrySerializer
        return CountryRelationSerializer

class RegionKeyFigureFilter(filters.FilterSet):
    region = filters.NumberFilter(name='region', lookup_expr='exact')
    class Meta:
        model = RegionKeyFigure
        fields = ('region',)

class RegionKeyFigureViewset(ReadOnlyVisibilityViewset):
    authentication_classes = (TokenAuthentication,)
    serializer_class = RegionKeyFigureSerializer
    filter_class = RegionKeyFigureFilter
    visibility_model_class = RegionKeyFigure

class CountryKeyFigureFilter(filters.FilterSet):
    country = filters.NumberFilter(name='country', lookup_expr='exact')
    class Meta:
        model = CountryKeyFigure
        fields = ('country',)

class CountryKeyFigureViewset(ReadOnlyVisibilityViewset):
    authentication_classes = (TokenAuthentication,)
    serializer_class = CountryKeyFigureSerializer
    filter_class = CountryKeyFigureFilter
    visibility_model_class = CountryKeyFigure

class RegionSnippetFilter(filters.FilterSet):
    region = filters.NumberFilter(name='region', lookup_expr='exact')
    class Meta:
        model = RegionSnippet
        fields = ('region',)

class RegionSnippetViewset(ReadOnlyVisibilityViewset):
    authentication_classes = (TokenAuthentication,)
    serializer_class = RegionSnippetSerializer
    filter_class = RegionSnippetFilter
    visibility_model_class = RegionSnippet

class CountrySnippetFilter(filters.FilterSet):
    country = filters.NumberFilter(name='country', lookup_expr='exact')
    class Meta:
        model = CountrySnippet
        fields = ('country',)

class CountrySnippetViewset(ReadOnlyVisibilityViewset):
    authentication_classes = (TokenAuthentication,)
    serializer_class = CountrySnippetSerializer
    filter_class = CountrySnippetFilter
    visibility_model_class = CountrySnippet

class DistrictFilter(filters.FilterSet):
    class Meta:
        model = District
        fields = ('country',)


class DistrictViewset(viewsets.ReadOnlyModelViewSet):
    queryset = District.objects.all()
    filter_class = DistrictFilter

    def get_serializer_class(self):
        if self.action == 'list':
            return MiniDistrictSerializer
        else:
            return DistrictSerializer


class EventFilter(filters.FilterSet):
    dtype = filters.NumberFilter(name='dtype', lookup_expr='exact')
    is_featured = filters.BooleanFilter(name='is_featured')
    countries__in = ListFilter(name='countries__id')
    regions__in = ListFilter(name='regions__id')
    id = filters.NumberFilter(name='id', lookup_expr='exact')
    class Meta:
        model = Event
        fields = {
            'disaster_start_date': ('exact', 'gt', 'gte', 'lt', 'lte'),
            'created_at': ('exact', 'gt', 'gte', 'lt', 'lte'),
        }

class EventViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Event.objects.all()
    def get_serializer_class(self):
        if self.action == 'list':
            return ListEventSerializer
        else:
            return DetailEventSerializer
    ordering_fields = ('disaster_start_date', 'created_at', 'name', 'summary', 'num_affected', 'glide', 'ifrc_severity_level',)
    filter_class = EventFilter

class EventSnippetFilter(filters.FilterSet):
    event = filters.NumberFilter(name='event', lookup_expr='exact')
    class Meta:
        model = Snippet
        fields = ('event',)

class EventSnippetViewset(ReadOnlyVisibilityViewset):
    authentication_classes = (TokenAuthentication,)
    serializer_class = SnippetSerializer
    filter_class = EventSnippetFilter
    visibility_model_class = Snippet

class SituationReportTypeViewset(viewsets.ReadOnlyModelViewSet):
    queryset = SituationReportType.objects.all()
    serializer_class = SituationReportTypeSerializer
    ordering_fields = ('type',)

class SituationReportFilter(filters.FilterSet):
    event = filters.NumberFilter(name='event', lookup_expr='exact')
    type = filters.NumberFilter(name='type', lookup_expr='exact')
    class Meta:
        model = SituationReport
        fields = {
            'name': ('exact',),
            'created_at': ('exact', 'gt', 'gte', 'lt', 'lte'),
        }

class SituationReportViewset(ReadOnlyVisibilityViewset):
    authentication_classes = (TokenAuthentication,)
    serializer_class = SituationReportSerializer
    ordering_fields = ('created_at', 'name',)
    filter_class = SituationReportFilter
    visibility_model_class = SituationReport

class AppealFilter(filters.FilterSet):
    atype = filters.NumberFilter(name='atype', lookup_expr='exact')
    dtype = filters.NumberFilter(name='dtype', lookup_expr='exact')
    country = filters.NumberFilter(name='country', lookup_expr='exact')
    region = filters.NumberFilter(name='region', lookup_expr='exact')
    code = filters.CharFilter(name='code', lookup_expr='exact')
    status = filters.NumberFilter(name='status', lookup_expr='exact')
    id = filters.NumberFilter(name='id', lookup_expr='exact')
    class Meta:
        model = Appeal
        fields = {
            'start_date': ('exact', 'gt', 'gte', 'lt', 'lte'),
            'end_date': ('exact', 'gt', 'gte', 'lt', 'lte'),
        }

class AppealViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Appeal.objects.all()
    serializer_class = AppealSerializer
    ordering_fields = ('start_date', 'end_date', 'name', 'aid', 'dtype', 'num_beneficiaries', 'amount_requested', 'amount_funded', 'status', 'atype', 'event',)
    filter_class = AppealFilter

    def remove_unconfirmed_event(self, obj):
        if obj['needs_confirmation']:
            obj['event'] = None
        return obj

    def remove_unconfirmed_events(self, objs):
        return [self.remove_unconfirmed_event(obj) for obj in objs]

    # Overwrite retrieve, list to exclude the event if it requires confirmation
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(self.remove_unconfirmed_events(serializer.data))

        serializer = self.get_serializer(queryset, many=True)
        return Response(self.remove_unconfirmed_events(serializer.data))

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(self.remove_unconfirmed_event(serializer.data))

class AppealDocumentFilter(filters.FilterSet):
    appeal = filters.NumberFilter(name='appeal', lookup_expr='exact')
    appeal__in = ListFilter(name='appeal__id')
    class Meta:
        model = AppealDocument
        fields = {
            'name': ('exact',),
            'created_at': ('exact', 'gt', 'gte', 'lt', 'lte'),
        }

class AppealDocumentViewset(viewsets.ReadOnlyModelViewSet):
    queryset = AppealDocument.objects.all()
    serializer_class = AppealDocumentSerializer
    ordering_fields = ('created_at', 'name',)
    filter_class = AppealDocumentFilter

class ProfileViewset(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)

class UserViewset(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def get_queryset(self):
        return User.objects.filter(pk=self.request.user.pk)

class FieldReportFilter(filters.FilterSet):
    dtype = filters.NumberFilter(name='dtype', lookup_expr='exact')
    user = filters.NumberFilter(name='user', lookup_expr='exact')
    countries__in = ListFilter(name='countries__id')
    regions__in = ListFilter(name='regions__id')
    id = filters.NumberFilter(name='id', lookup_expr='exact')
    class Meta:
        model = FieldReport
        fields = {
            'created_at': ('exact', 'gt', 'gte', 'lt', 'lte'),
            'updated_at': ('exact', 'gt', 'gte', 'lt', 'lte'),
        }

class FieldReportViewset(ReadOnlyVisibilityViewset):
    authentication_classes = (TokenAuthentication,)
    visibility_model_class = FieldReport
    def get_serializer_class(self):
        if self.action == 'list':
            return ListFieldReportSerializer
        else:
            return DetailFieldReportSerializer

    ordering_fields = ('summary', 'event', 'dtype', 'created_at', 'updated_at')
    filter_class = FieldReportFilter

class GenericFieldReportView(GenericAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = FieldReport.objects.all()

    def serialize(self, data, instance=None):
        # Replace integer values for Int Enum types.
        # Otherwise, validation will fail.
        # This applies to visibility and request choices.
        if data['visibility'] == 2 or data['visibility'] == '2':
            data['visibility'] = VisibilityChoices.IFRC
        elif data['visibility'] == 3 or data['visibility'] == '3':
            data['visibility'] = VisibilityChoices.PUBLIC
        else:
            data['visibility'] = VisibilityChoices.MEMBERSHIP

        request_choices = [
            'bulletin',
            'dref',
            'appeal',
            'rdrt',
            'fact',
            'ifrc_staff',
            'eru_base_camp',
            'eru_basic_health_care',
            'eru_it_telecom',
            'eru_logistics',
            'eru_deployment_hospital',
            'eru_referral_hospital',
            'eru_relief',
            'eru_water_sanitation_15',
            'eru_water_sanitation_40',
            'eru_water_sanitation_20',
        ]
        for prop in request_choices:
            if prop in data:
                if data[prop] == 1 or data[prop] == '1':
                    data[prop] = RequestChoices.REQUESTED
                elif data[prop] == 2 or data[prop] == '2':
                    data[prop] = RequestChoices.PLANNED
                elif data[prop] == 3 or data[prop] == '3':
                    data[prop] = RequestChoices.COMPLETE
                else:
                    data[prop] = RequestChoices.NO

        if instance is not None:
            serializer = CreateFieldReportSerializer(instance, data=data)
        else:
            serializer = CreateFieldReportSerializer(data=data)
        return serializer

    def map_foreign_key_relations(self, data):
        # The request data object will come with a lot of relation mappings.
        # For foreign key, we want to replace instance ID's with querysets.

        # Query foreign key relations, these are attached on model save/update.
        mappings = [
            ('user', User),
            ('dtype', DisasterType),
            ('event', Event),
        ]
        for (prop, model) in mappings:
            if prop in data and data[prop] is not None:
                try:
                    data[prop] = model.objects.get(pk=data[prop])
                except:
                    raise BadRequest('Valid %s is required' % prop)
            elif prop is not 'event':
                raise BadRequest('Valid %s is required' % prop)

        return data

    def map_many_to_many_relations(self, data):
        # Query many-to-many mappings. These are removed from the data object,
        # So they can be added later.
        mappings = [
            ('countries', Country),
            ('regions', Region),
            ('districts', District),
        ]

        locations = {}
        for (prop, model) in mappings:
            if prop in data and hasattr(data[prop], '__iter__') and len(data[prop]):
                locations[prop] = list(data[prop])
            if prop in data:
                del data[prop]

        # Sources, actions, and contacts
        mappings = [
            ('actions_taken'),
            ('contacts'),
            ('sources'),
        ]

        meta = {}
        for (prop) in mappings:
            if prop in data and hasattr(data[prop], '__iter__') and len(data[prop]):
                meta[prop] = list(data[prop])
            if prop in data:
                del data[prop]

        return data, locations, meta

    def save_locations(self, instance, locations, is_update=False):
        if is_update:
            instance.districts.clear()
            instance.countries.clear()
            instance.regions.clear()
        if 'districts' in locations:
            instance.districts.add(*locations['districts'])
        if 'countries' in locations:
            instance.countries.add(*locations['countries'])
            # Add countries in automatically, based on regions
            countries = Country.objects.filter(pk__in=locations['countries'])
            instance.regions.add(*[country.region for country in countries if (
                country.region is not None
            )])

    def save_meta(self, fieldreport, meta, is_update=False):
        if is_update:
            ActionsTaken.objects.filter(field_report=fieldreport).delete()
            FieldReportContact.objects.filter(field_report=fieldreport).delete()
            Source.objects.filter(field_report=fieldreport).delete()

        if 'actions_taken' in meta:
            for action in meta['actions_taken']:
                actions = action['actions']
                del action['actions']
                actions_taken = ActionsTaken.objects.create(field_report=fieldreport, **action)
                actions_taken.actions.add(*actions)

        if 'contacts' in meta:
            FieldReportContact.objects.bulk_create(
                [FieldReportContact(field_report=fieldreport, **fields) for fields in meta['contacts']]
            )

        if 'sources' in meta:
            for source in meta['sources']:
                stype, created = SourceType.objects.get_or_create(name=source['stype'])
                source['stype'] = stype
            Source.objects.bulk_create(
                [Source(field_report=fieldreport, **fields) for fields in meta['sources']]
            )

class CreateFieldReport(CreateAPIView, GenericFieldReportView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = FieldReport.objects.all()
    serializer_class = CreateFieldReportSerializer

    def create_event(self, report):
        event = Event.objects.create(
            name=report.summary,
            dtype=report.dtype,
            disaster_start_date=report.start_date,
            auto_generated=True,
            auto_generated_source=SOURCES['new_report'],
        )
        report.event = event
        report.save()
        return event

    def create(self, request):
        serializer = self.serialize(request.data)
        if not serializer.is_valid():
            raise BadRequest(serializer.errors)

        data = self.map_foreign_key_relations(request.data)
        data, locations, meta = self.map_many_to_many_relations(data)

        try:
            fieldreport = FieldReport.objects.create(**data)
        except:
            raise BadRequest('Could not create field report')

        ### Creating relations ###
        # These are *not* handled in a transaction block.
        # The data model for these is very permissive. We're more interested in the
        # Numerical data being there than not.
        errors = []
        try:
            self.save_locations(fieldreport, locations)
        except Exception as e:
            errors.append(e)

        try:
            self.save_meta(fieldreport, meta)
        except Exception as e:
            errors.append(e)

        # If the report doesn't have an emergency attached, create one.
        if fieldreport.event is None:
            event = self.create_event(fieldreport)
            try:
                self.save_locations(event, locations)
            except Exception as e:
                errors.append(e)

        if len(errors):
            logger.error('%s errors creating new field reports' % len(errors))
            for error in errors:
                logger.error(str(error)[:200])

        return Response({'id': fieldreport.id}, status=HTTP_201_CREATED)

class UpdateFieldReport(UpdateAPIView, GenericFieldReportView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = FieldReport.objects.all()
    serializer_class = CreateFieldReportSerializer

    def partial_update(self, request, *args, **kwargs):
        self.update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serialize(request.data, instance=instance)
        if not serializer.is_valid():
            raise BadRequest(serializer.errors)

        data = self.map_foreign_key_relations(request.data)
        data, locations, meta = self.map_many_to_many_relations(data)

        try:
            serializer.save()
        except Exception as e:
            raise BadRequest('Could not update field report')

        errors = []
        try:
            self.save_locations(instance, locations, is_update=True)
        except Exception as e:
            errors.append(e)

        try:
            self.save_meta(instance, meta, is_update=True)
        except Exception as e:
            errors.append(e)

        if len(errors):
            logger.error('%s errors creating new field reports' % len(errors))
            for error in errors:
                logger.error(str(error)[:200])

        return Response({'id': instance.id}, status=HTTP_200_OK)
