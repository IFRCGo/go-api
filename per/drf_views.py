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
from api.exceptions import BadRequest
from api.view_filters import ListFilter
from api.visibility_class import ReadOnlyVisibilityViewset
from deployments.models import Personnel

from .models import (
    Form, FormData
)

from .serializers import (
    ListFormSerializer, ListFormDataSerializer,
)

# stackoverflow.com/questions/35581292/how-to-filter-user-related-records-with-permissions-in-django-rest-framework
# www.django-rest-framework.org/api-guide/filtering/#djangoobjectpermissionsfilter
class FormViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Form.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == 'list':
            return ListFormSerializer
#       else:
#           return DetailFormSerializer
        ordering_fields = ('name',)

class FormDataViewset(viewsets.ReadOnlyModelViewSet):
    queryset = FormData.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def get_serializer_class(self):
        if self.action == 'list':
            return ListFormDataSerializer
#       else:
#           return DetailFormDataSerializer
        ordering_fields = ('name',)
