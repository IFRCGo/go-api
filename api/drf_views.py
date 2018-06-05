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

class EventViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Event.objects.all()
    def get_serializer_class(self):
        if self.action == 'list':
            return ListEventSerializer
        else:
            return DetailEventSerializer

    filter_backends = (filters.DjangoFilterBackend,)
    ordering_fields = ('disaster_start_date', 'created_at', 'name', 'dtype', 'summary', 'num_affected', 'alert_level', 'glide'),
    filter_fields = {
        'disaster_start_date': ('exact', 'gt', 'gte', 'lt', 'lte'),
        'created_at': ('exact', 'gt', 'gte', 'lt', 'lte'),
    }

class SituationReportViewset(viewsets.ReadOnlyModelViewSet):
    queryset = SituationReport.objects.all()
    serializer_class = SituationReportSerializer

class AppealViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Appeal.objects.all()
    serializer_class = AppealSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    ordering_fields = ('start_date', 'end_date', 'name', 'aid', 'dtype', 'num_beneficiaries', 'amount_requested', 'amount_funded',)
    filter_fields = {
        'start_date': ('exact', 'gt', 'gte', 'lt', 'lte'),
        'end_date': ('exact', 'gt', 'gte', 'lt', 'lte'),
    }

class AppealDocumentViewset(viewsets.ReadOnlyModelViewSet):
    queryset = AppealDocument.objects.all()
    serializer_class = AppealDocumentSerializer

class ProfileViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

class UserViewset(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class FieldReportViewset(viewsets.ModelViewSet):
    queryset = FieldReport.objects.all()
    def get_serializer_class(self):
        if self.action == 'list':
            return ListFieldReportSerializer
        else:
            return DetailFieldReportSerializer
