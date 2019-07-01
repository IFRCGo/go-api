from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK
from rest_framework.generics import GenericAPIView, CreateAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from django.contrib import admin
from django.db import models
from django.utils import timezone
from django_filters import rest_framework as filters
from api.exceptions import BadRequest
from api.view_filters import ListFilter
from api.visibility_class import ReadOnlyVisibilityViewset
from deployments.models import Personnel
from django.db.models import Count, Q
from .admin_classes import RegionRestrictedAdmin
from api.models import Country, Region
from api.serializers import (MiniCountrySerializer, NotCountrySerializer)
from django.conf import settings
from datetime import datetime
import pytz

from .models import (
    Draft, Form, FormData, NSPhase
)

from .serializers import (
    ListDraftSerializer,
    FormStatSerializer,
    ListFormSerializer,
    ListFormDataSerializer,
    ShortFormSerializer,
    EngagedNSPercentageSerializer,
    GlobalPreparednessSerializer,
    NSPhaseSerializer,
)

class DraftFilter(filters.FilterSet):
    user = filters.NumberFilter(name='user', lookup_expr='exact')
    code = filters.CharFilter(name='code', lookup_expr='exact')
    id = filters.NumberFilter(name='id', lookup_expr='exact')
    class Meta:
        model = Draft
        fields = {
            'user': ('exact',),
            'code': ('exact',),
        }

class DraftViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Draft.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    filter_class = DraftFilter
    # It is not checked whether this user is the same as the saver. Maybe (for helpers) it is not needed really.

    def get_serializer_class(self):
        if self.action == 'list':
            return ListDraftSerializer
#       else:
#           return DetailDraftSerializer
        ordering_fields = ('name',)

class FormViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Form.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions
    get_filtered_queryset = RegionRestrictedAdmin.get_filtered_queryset
    # It is not checked whether this user is the same as the saver. Maybe (for helpers) it is not needed really.

    def get_queryset(self):
        queryset =  Form.objects.all()
        return self.get_filtered_queryset(self.request, queryset, 1)

    def get_serializer_class(self):
        if self.action == 'list':
            return ListFormSerializer
#       else:
#           return DetailFormSerializer
        ordering_fields = ('name',)

class FormDataFilter(filters.FilterSet):
    form = filters.NumberFilter(name='form', lookup_expr='exact')
    id = filters.NumberFilter(name='id', lookup_expr='exact')
    class Meta:
        model = FormData
        fields = {
            'form': ('exact', 'gt', 'gte', 'lt', 'lte'),
        }

class FormDataViewset(viewsets.ReadOnlyModelViewSet):
    queryset = FormData.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions
    get_filtered_queryset = RegionRestrictedAdmin.get_filtered_queryset
    filter_class = FormDataFilter

    def get_queryset(self):
        queryset =  FormData.objects.all()
        return self.get_filtered_queryset(self.request, queryset, 2)

    def get_serializer_class(self):
        if self.action == 'list':
            return ListFormDataSerializer
#       else:
#           return DetailFormDataSerializer
        ordering_fields = ('name',)

class FormCountryViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions
    get_filtered_queryset = RegionRestrictedAdmin.get_filtered_queryset
    serializer_class = MiniCountrySerializer

    def get_queryset(self):
        queryset =  Country.objects.all()
        return self.get_filtered_queryset(self.request, queryset, 3)

class FormStatViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Form.objects.all()
    authentication_classes = (TokenAuthentication,)

    def get_queryset(self):
        queryset =  Form.objects.all()
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return FormStatSerializer
#       else:
#           return DetailFormSerializer
        ordering_fields = ('name',)

class FormPermissionViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions
    get_filtered_queryset = RegionRestrictedAdmin.get_filtered_queryset
    serializer_class = NotCountrySerializer

    def get_queryset(self):
        queryset =  Country.objects.all()
        if self.get_filtered_queryset(self.request, queryset, 3).exists():
            return [Country.objects.get(id=1)]
        else:
            return Country.objects.none()

class CountryDuedateViewset(viewsets.ReadOnlyModelViewSet):
    """Countries and their forms which were submitted since last due date"""

    queryset = Form.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    country = MiniCountrySerializer
    serializer_class = ShortFormSerializer

    def get_queryset(self):
        last_duedate = settings.PER_LAST_DUEDATE
        next_duedate = settings.PER_NEXT_DUEDATE
        timezone = pytz.timezone("Europe/Zurich")
        if not last_duedate:
            last_duedate = timezone.localize(datetime(2000, 11, 15, 9, 59, 25, 0))
        if not next_duedate:
            next_duedate = timezone.localize(datetime(2222, 11, 15, 9, 59, 25, 0))
        queryset =  Form.objects.filter(submitted_at__gt=last_duedate)
        if queryset.exists():
            return queryset
        else:
            return Form.objects.none()

class EngagedNSPercentageViewset(viewsets.ReadOnlyModelViewSet):
    """National Societies engaged in per process"""
    queryset = Region.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = EngagedNSPercentageSerializer

    def get_queryset(self):
        last_duedate = settings.PER_LAST_DUEDATE
        next_duedate = settings.PER_NEXT_DUEDATE
        timezone = pytz.timezone("Europe/Zurich")
        if not last_duedate:
            last_duedate = timezone.localize(datetime(2000, 11, 15, 9, 59, 25, 0))
        if not next_duedate:
            next_duedate = timezone.localize(datetime(2222, 11, 15, 9, 59, 25, 0))
        queryset1 = Region.objects.all().annotate(Count('country')).values('id', 'country__count')
        queryset2 = Region.objects.filter(country__form__submitted_at__gt=last_duedate) \
                    .values('id').annotate(forms_sent=Count('country'))
        # We merge the 2 lists (all and forms_sent), like {'id': 2, 'country__count': 37} and {'id': 2, 'forms_sent': 2} to
        #                                                 {'id': 2, 'country__count': 37, 'forms_sent': 2}, even with zeroes.
        result=[]
        for i in queryset1:
            i['forms_sent'] = 0
            for j in queryset2:
                if int(j['id']) == int(i['id']):
                # if this never occurs, (so no form-sender country in this region), forms_sent remain 0
                    i['forms_sent'] = j['forms_sent']
            result.append(i)
        # [{'id': 0, 'country__count': 49, 'forms_sent': 0}, {'id': 1, 'country__count': 35, 'forms_sent': 1}...
        return result

class GlobalPreparednessViewset(viewsets.ReadOnlyModelViewSet):
    """Global Preparedness Highlights"""
    queryset = Form.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = GlobalPreparednessSerializer

    def get_queryset(self):
        last_duedate = settings.PER_LAST_DUEDATE
        next_duedate = settings.PER_NEXT_DUEDATE
        timezone = pytz.timezone("Europe/Zurich")
        if not last_duedate:
            last_duedate = timezone.localize(datetime(2000, 11, 15, 9, 59, 25, 0))
        if not next_duedate:
            next_duedate = timezone.localize(datetime(2222, 11, 15, 9, 59, 25, 0))
        queryset = FormData.objects.filter(form__submitted_at__gt=last_duedate, selected_option=7).select_related('form')
        result=[]
        for i in queryset:
            j = {'id': i.form.id}
            j.update({'code': i.form.code})
            j.update({'question_id': i.question_id})
            result.append(j)
        return result

class NSPhaseFilter(filters.FilterSet):
    country = filters.NumberFilter(name='country', lookup_expr='exact')
    id = filters.NumberFilter(name='id', lookup_expr='exact')

    class Meta:
        model = NSPhase
        fields = {
            'updated_at': ('exact', 'gt', 'gte', 'lt', 'lte'),
        }

class NSPhaseViewset(viewsets.ReadOnlyModelViewSet):
    """NS PER Process Phase Viewset"""
    queryset = NSPhase.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = NSPhaseSerializer
    filter_class = NSPhaseFilter

    def filter_queryset(self, queryset):
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        # Giving a default value when queryset is empty - would like to have country parameter also
        if not queryset:
            queryset = "{'phase': '0'}"
        return queryset
