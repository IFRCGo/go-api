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
#from django.db.models import Q
#from .admin_classes import RegionRestrictedAdmin
from api.models import Country
#from api.serializers import (MiniCountrySerializer, NotCountrySerializer)

from .models import (
    Project
)

from .serializers import (
    ProjectSerializer
)

class ProjectFilter(filters.FilterSet):
    form = filters.NumberFilter(name='form', lookup_expr='exact')
    id = filters.NumberFilter(name='id', lookup_expr='exact')
    class Meta:
        model = Project
        fields = {
            'form': ('exact', 'gt', 'gte', 'lt', 'lte'),
        }

class ProjectViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Project.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    # get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions
    # get_filtered_queryset = RegionRestrictedAdmin.get_filtered_queryset
    filter_class = ProjectFilter
    serializer_class = ProjectSerializer
    ordering_fields = ('name',)

#    def get_queryset(self):
#        queryset =  Project.objects.all()
#        return self.get_filtered_queryset(self.request, queryset, 2)

