from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from django_filters import rest_framework as filters
from django.contrib.auth.models import User
from .models import (
    DisasterType,
    Region,
    Country,
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
    CountrySerializer,
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
    serializer_class = RegionSerializer

class CountryViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer

class EventFilter(filters.FilterSet):
    dtype = filters.NumberFilter(name='dtype', lookup_expr='exact')
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
    ordering_fields = ('disaster_start_date', 'created_at', 'name', 'dtype', 'summary', 'num_affected', 'alert_level', 'glide'),
    filter_class = EventFilter

class SituationReportViewset(viewsets.ReadOnlyModelViewSet):
    queryset = SituationReport.objects.all()
    serializer_class = SituationReportSerializer

class AppealFilter(filters.FilterSet):
    atype = filters.NumberFilter(name='atype', lookup_expr='exact')
    dtype = filters.NumberFilter(name='dtype', lookup_expr='exact')
    country = filters.NumberFilter(name='country', lookup_expr='exact')
    region = filters.NumberFilter(name='region', lookup_expr='exact')
    class Meta:
        model = Appeal
        fields = {
            'start_date': ('exact', 'gt', 'gte', 'lt', 'lte'),
            'end_date': ('exact', 'gt', 'gte', 'lt', 'lte'),
        }

class AppealViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Appeal.objects.all()
    serializer_class = AppealSerializer
    ordering_fields = ('start_date', 'end_date', 'name', 'aid', 'dtype', 'num_beneficiaries', 'amount_requested', 'amount_funded',)
    filter_class = AppealFilter

class AppealDocumentViewset(viewsets.ReadOnlyModelViewSet):
    queryset = AppealDocument.objects.all()
    serializer_class = AppealDocumentSerializer

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

    ordering_fields = ('summary', 'created_at', 'updated_at')
    filter_class = FieldReportFilter
