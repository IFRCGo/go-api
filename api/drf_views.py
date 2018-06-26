from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets
from django_filters import rest_framework as filters
from django.contrib.auth.models import User
from .view_filters import ListFilter
from .models import (
    DisasterType,

    Region,
    RegionKeyFigure,
    RegionSnippet,

    Country,
    CountryKeyFigure,
    CountrySnippet,

    District,

    Event,
    SituationReport,
    Appeal,
    AppealDocument,
    Profile,
    FieldReport,
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

    ListEventSerializer,
    DetailEventSerializer,
    SituationReportSerializer,
    AppealSerializer,
    AppealDocumentSerializer,
    UserSerializer,
    ProfileSerializer,
    ListFieldReportSerializer,
    DetailFieldReportSerializer,
)

class DisasterTypeViewset(viewsets.ReadOnlyModelViewSet):
    queryset = DisasterType.objects.all()
    serializer_class = DisasterTypeSerializer

class RegionViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Region.objects.all()
    def get_serializer_class(self):
        if self.action == 'list':
            return RegionSerializer
        return RegionRelationSerializer

class CountryViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.all()
    def get_serializer_class(self):
        if self.action == 'list':
            return CountrySerializer
        return CountryRelationSerializer

class RegionKeyFigureFilter(filters.FilterSet):
    region = filters.NumberFilter(name='region', lookup_expr='exact')
    class Meta:
        model = RegionKeyFigure
        fields = ('region',)

class RegionKeyFigureViewset(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication,)
    serializer_class = RegionKeyFigureSerializer
    filter_class = RegionKeyFigureFilter
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return RegionKeyFigure.objects.all()
        return RegionKeyFigure.objects.filter(visibility=3)

class CountryKeyFigureFilter(filters.FilterSet):
    country = filters.NumberFilter(name='country', lookup_expr='exact')
    class Meta:
        model = CountryKeyFigure
        fields = ('country',)

class CountryKeyFigureViewset(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication,)
    serializer_class = CountryKeyFigureSerializer
    filter_class = CountryKeyFigureFilter
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return CountryKeyFigure.objects.all()
        return CountryKeyFigure.objects.filter(visibility=3)

class RegionSnippetFilter(filters.FilterSet):
    region = filters.NumberFilter(name='region', lookup_expr='exact')
    class Meta:
        model = RegionSnippet
        fields = ('region',)

class RegionSnippetViewset(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication,)
    serializer_class = RegionSnippetSerializer
    filter_class = RegionSnippetFilter
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return RegionSnippet.objects.all()
        return RegionSnippet.objects.filter(visibility=3)

class CountrySnippetFilter(filters.FilterSet):
    country = filters.NumberFilter(name='country', lookup_expr='exact')
    class Meta:
        model = CountrySnippet
        fields = ('country',)

class CountrySnippetViewset(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (TokenAuthentication,)
    serializer_class = CountrySnippetSerializer
    filter_class = CountrySnippetFilter
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return CountrySnippet.objects.all()
        return CountrySnippet.objects.filter(visibility=3)

class DistrictViewset(viewsets.ReadOnlyModelViewSet):
    queryset = District.objects.all()
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
    ordering_fields = ('disaster_start_date', 'created_at', 'name', 'summary', 'num_affected', 'glide', 'alert_level',)
    filter_class = EventFilter

class SituationReportFilter(filters.FilterSet):
    event = filters.NumberFilter(name='event', lookup_expr='exact')
    class Meta:
        model = SituationReport
        fields = {
            'name': ('exact',),
            'created_at': ('exact', 'gt', 'gte', 'lt', 'lte'),
        }

class SituationReportViewset(viewsets.ReadOnlyModelViewSet):
    queryset = SituationReport.objects.all()
    serializer_class = SituationReportSerializer
    ordering_fields = ('created_at', 'name',)
    filter_class = SituationReportFilter

class AppealFilter(filters.FilterSet):
    atype = filters.NumberFilter(name='atype', lookup_expr='exact')
    dtype = filters.NumberFilter(name='dtype', lookup_expr='exact')
    country = filters.NumberFilter(name='country', lookup_expr='exact')
    region = filters.NumberFilter(name='region', lookup_expr='exact')
    code = filters.CharFilter(name='code', lookup_expr='exact')
    status = filters.NumberFilter(name='status', lookup_expr='exact')
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
    class Meta:
        model = FieldReport
        fields = {
            'created_at': ('exact', 'gt', 'gte', 'lt', 'lte'),
            'updated_at': ('exact', 'gt', 'gte', 'lt', 'lte'),
        }

class FieldReportViewset(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return FieldReport.objects.all()
        # for unauthenticated users, return public field reports
        return FieldReport.objects.filter(visibility=3)

    def get_serializer_class(self):
        if self.action == 'list':
            return ListFieldReportSerializer
        else:
            return DetailFieldReportSerializer

    ordering_fields = ('summary', 'event', 'dtype', 'created_at', 'updated_at')
    filter_class = FieldReportFilter
