from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK
from rest_framework.generics import GenericAPIView, CreateAPIView, UpdateAPIView
from rest_framework.views import APIView
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

from django.contrib.auth.models import User, Group
from .models import (
    Draft, Form, FormData, NSPhase, WorkPlan, Overview, NiceDocument
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
    MiniUserSerializer,
    WorkPlanSerializer,
    OverviewSerializer,
    ListNiceDocSerializer,
)

class DraftFilter(filters.FilterSet):
    user = filters.NumberFilter(name='user', lookup_expr='exact')
    code = filters.CharFilter(name='code', lookup_expr='exact')
    country = filters.CharFilter(name='country', lookup_expr='exact')
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
    """Can use 'new' GET parameter for using data only after the last due_date"""
    # Duplicate of PERDocsViewset
    queryset = FormData.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions
    get_filtered_queryset = RegionRestrictedAdmin.get_filtered_queryset
    filter_class = FormDataFilter

    def get_queryset(self):
        queryset = FormData.objects.all()
        cond1 = Q()
        cond2 = Q() # This way only those conditions will be effective which we set later:
        if 'new' in self.request.query_params.keys():
            last_duedate = settings.PER_LAST_DUEDATE
            timezone = pytz.timezone("Europe/Zurich")
            if not last_duedate:
                last_duedate = timezone.localize(datetime(2000, 11, 15, 9, 59, 25, 0))
            cond1 = Q(form__submitted_at__gt=last_duedate)
        if 'country' in self.request.query_params.keys():
            cid = self.request.query_params.get('country', None) or 0
            country = Country.objects.filter(pk=cid)
            if country:
                cond2 = Q(form__country_id=country[0].id)
        queryset = FormData.objects.filter(cond1 & cond2)
        if queryset.exists():
            queryset = self.get_filtered_queryset(self.request, queryset, 2)
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return ListFormDataSerializer
#       else:
#           return DetailFormDataSerializer
        ordering_fields = ('name',)

class FormCountryViewset(viewsets.ReadOnlyModelViewSet):
    """shows the (PER editable) countries for a user."""
    queryset = Country.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions
    get_filtered_queryset = RegionRestrictedAdmin.get_filtered_queryset
    serializer_class = MiniCountrySerializer

    def get_queryset(self):
        queryset =  Country.objects.all()
        return self.get_filtered_queryset(self.request, queryset, 3)

class PERDocsFilter(filters.FilterSet):
    id = filters.NumberFilter(name='id', lookup_expr='exact')
    class Meta:
        model = NiceDocument
        fields = {
            'id': ('exact',),
        }

class PERDocsViewset(viewsets.ReadOnlyModelViewSet):
    """ To collect PER Documents """
    # Duplicate of FormDataViewset
    queryset = NiceDocument.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions
    get_filtered_queryset = RegionRestrictedAdmin.get_filtered_queryset
    filter_class = PERDocsFilter

    def get_queryset(self):
        queryset = NiceDocument.objects.all()
        cond1 = Q()
        cond2 = Q()
        cond3 = Q() # This way only those conditions will be effective which we set later:
        if 'new' in self.request.query_params.keys():
            last_duedate = settings.PER_LAST_DUEDATE
            timezone = pytz.timezone("Europe/Zurich")
            if not last_duedate:
                last_duedate = timezone.localize(datetime(2000, 11, 15, 9, 59, 25, 0))
            cond1 = Q(created_at__gt=last_duedate)
        if 'country' in self.request.query_params.keys():
            cid = self.request.query_params.get('country', None) or 0
            country = Country.objects.filter(pk=cid)
            if country:
                cond2 = Q(country_id=country[0].id)
        if 'visible' in self.request.query_params.keys():
            cond3 = Q(visibility=1)
        queryset = NiceDocument.objects.filter(cond1 & cond2 & cond3)
        if queryset.exists():
            queryset = self.get_filtered_queryset(self.request, queryset, 4)
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return ListNiceDocSerializer
#       else:
#           return DetailFormDataSerializer
        ordering_fields = ('name', 'country',)


# Not used:
# class FormCountryUsersViewset(viewsets.ReadOnlyModelViewSet):
#    """Names and email addresses of the PER responsible users in a GIVEN country.
#    Without country parameter it gives back empty set, not error."""
#    queryset = User.objects.all()
#    authentication_classes = (TokenAuthentication,)
#    permission_classes = (IsAuthenticated,)
#    serializer_class = MiniUserSerializer
#
#    def get_queryset(self):
#        country = Country.objects.filter(pk=self.request.query_params.get('country', None))
#        if country: # First we try to search a country PER admin
#            regid = country.values('region')[0]['region']
#            regionname = ['Africa', 'Americas', 'Asia Pacific', 'Europe', 'MENA'][regid]
#            countryname = country.values('name')[0]['name']
#            cond1 = Q(groups__name__contains='PER')
#            cond2 = Q(groups__name__icontains=countryname)
#            queryset = User.objects.filter(cond1 & cond2).values('first_name', 'last_name', 'email')
#            if queryset.exists():
#                return queryset
#            else: # Now let's try to get a Region admin for that country
#                cond2 = Q(groups__name__icontains=regionname)
#                cond3 = Q(groups__name__contains='Region')
#                queryset = User.objects.filter(cond1 & cond2 & cond3).values('first_name', 'last_name', 'email')
#                if queryset.exists():
#                    return queryset
#                else: # Finally we can show only PER Core admins
#                    cond2 = Q(groups__name__contains='Core Admins') # region also can come here
#                    queryset = User.objects.filter(cond1 & cond2).values('first_name', 'last_name', 'email')
#                    if queryset.exists():
#                        return queryset
#        return User.objects.none()

class FormStatViewset(viewsets.ReadOnlyModelViewSet):
    """Shows name, code, country_id, language of filled forms"""
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
    """Shows if a user has permission to PER frontend tab or not"""
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
    # Some parts can be seen by public | NO authentication_classes = (TokenAuthentication,)
    # Some parts can be seen by public | NO permission_classes = (IsAuthenticated,)
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
                    .values('id').annotate(forms_sent=Count('country__form__code', distinct=True))
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
    phase = filters.NumberFilter(name='phase', lookup_expr='exact')
    id = filters.NumberFilter(name='id', lookup_expr='exact')

    class Meta:
        model = NSPhase
        fields = {
            'updated_at': ('exact', 'gt', 'gte', 'lt', 'lte'),
        }

class NSPhaseViewset(viewsets.ReadOnlyModelViewSet):
    """NS PER Process Phase Viewset"""
    queryset = NSPhase.objects.all()
    # Some parts can be seen by public | NO authentication_classes = (TokenAuthentication,)
    # Some parts can be seen by public | NO permission_classes = (IsAuthenticated,)
    serializer_class = NSPhaseSerializer
    filter_class = NSPhaseFilter

    def filter_queryset(self, queryset):
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        # Giving a default value when queryset is empty, with the given country_id (if exists)
        if not queryset and Country.objects.filter(pk = self.request.query_params.get('country', None)):
            j = {'id': -1}
            j.update({'country': Country.objects.get(pk = self.request.query_params.get('country', None))})
            j.update({'updated_at': pytz.timezone("Europe/Zurich").localize(datetime(2011, 11, 11, 1, 1, 1, 0))})
            j.update({'phase': 0})
            return [j]
        return queryset

class WorkPlanFilter(filters.FilterSet):
    id = filters.NumberFilter(name='id', lookup_expr='exact')
    country = filters.NumberFilter(name='country', lookup_expr='exact')
    class Meta:
        model = WorkPlan
        fields = {
            'id': ('exact',),
        }

class WorkPlanViewset(viewsets.ReadOnlyModelViewSet):
    """ PER Work Plan Viewset"""
    queryset = WorkPlan.objects.all()
    # Some parts can be seen by public | NO authentication_classes = (TokenAuthentication,)
    # Some parts can be seen by public | NO permission_classes = (IsAuthenticated,)
    filter_class = WorkPlanFilter
    serializer_class = WorkPlanSerializer

class OverviewFilter(filters.FilterSet):
    id = filters.NumberFilter(name='id', lookup_expr='exact')
    country = filters.NumberFilter(name='country', lookup_expr='exact')
    class Meta:
        model = Overview
        fields = {
            'id': ('exact',),
        }

class OverviewViewset(viewsets.ReadOnlyModelViewSet):
    """ PER Work Plan Viewset"""
    queryset = Overview.objects.all()
    # Some parts can be seen by public | NO authentication_classes = (TokenAuthentication,)
    # Some parts can be seen by public | NO permission_classes = (IsAuthenticated,)
    filter_class = OverviewFilter
    serializer_class = OverviewSerializer

