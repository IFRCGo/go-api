from drf_spectacular.utils import extend_schema
from rest_framework import response, status, views, viewsets

from .models import DomainWhitelist
from .serializers import (
    ChangePasswordSerializer,
    ChangeRecoverPasswordSerializer,
    DomainWhitelistSerializer,
    RegistrationSerializer,
)


class DomainWhitelistViewset(viewsets.ReadOnlyModelViewSet):
    queryset = DomainWhitelist.objects.filter(is_active=True)
    serializer_class = DomainWhitelistSerializer


class ChangeRecoverPasswordView(views.APIView):
    @extend_schema(request=ChangeRecoverPasswordSerializer, responses=None)
    def post(self, request, version=None):
        serializer = ChangeRecoverPasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data, status=status.HTTP_200_OK)


class ChangePasswordView(views.APIView):
    @extend_schema(request=ChangePasswordSerializer, responses=None)
    def post(self, request, version=None):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data, status=status.HTTP_200_OK)


class RegistrationView(views.APIView):

    @extend_schema(request=RegistrationSerializer, responses=RegistrationSerializer)
    def post(self, request, version=None):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data, status=status.HTTP_200_OK)
