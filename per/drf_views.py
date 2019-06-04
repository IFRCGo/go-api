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

from .models import (
    Form, FormData
)

from .serializers import (
    ListFormSerializer, ListFormDataSerializer,
)

class FormViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Form.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions
    get_filtered_queryset = RegionRestrictedAdmin.get_filtered_queryset

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
