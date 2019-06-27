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
from django.db.models import Q
from .admin_classes import RegionRestrictedAdmin
from api.models import Country
from api.serializers import (MiniCountrySerializer, NotCountrySerializer)
from django.conf import settings
from datetime import datetime
import pytz

from .models import (
    Draft, Form, FormData
)

from .serializers import (
    ListDraftSerializer, FormStatSerializer, ListFormSerializer, ListFormDataSerializer,
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
    queryset = Country.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = MiniCountrySerializer

    def get_queryset(self):
        last_deadline = settings.PER_LAST_DEADLINE
        next_deadline = settings.PER_NEXT_DEADLINE
        timezone = pytz.timezone("Europe/Zurich")
        if not last_deadline:
            last_deadline = timezone.localize(datetime(2000, 11, 15, 9, 59, 25, 111111))
        if not next_deadline:
            next_deadline = timezone.localize(datetime(2222, 11, 15, 9, 59, 25, 111111))
        queryset =  Country.objects.filter(form__submitted_at__gt=last_deadline)
        if queryset.exists():
            return queryset
        else:
            return Country.objects.none()
