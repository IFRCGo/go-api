from rest_framework import (
    viewsets,
    views,
    response,
    status
)
from drf_spectacular.utils import extend_schema
from .models import DomainWhitelist
from .serializers import (
    DomainWhitelistSerializer,
    ChangePasswordSerializer
    status,
    response
)
from drf_spectacular.utils import extend_schema

from .models import DomainWhitelist
from .serializers import DomainWhitelistSerializer, RegistrationSerializer


class DomainWhitelistViewset(viewsets.ReadOnlyModelViewSet):
    queryset = DomainWhitelist.objects.filter(is_active=True)
    serializer_class = DomainWhitelistSerializer


class ChangePasswordView(views.APIView):
    @extend_schema(request=ChangePasswordSerializer, responses=None)
    def post(self, request, version=None):
        serializer = ChangePasswordSerializer(data=request.data)

class RegistrationView(views.APIView):

    @extend_schema(request=None, responses=RegistrationSerializer)
    def post(self, request, version=None):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(
            "OK", status=status.HTTP_200_OK
        )
