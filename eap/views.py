# Create your views here.

from rest_framework.response import Response
from rest_framework import (
    views,
    viewsets,
    permissions,
    mixins,
)
from .models import (
    EarlyActionIndicator,
    EAP,
    EAPDocument,
)
from .serializers import (
    EAPSerializer,
    EAPDocumentSerializer,
)


class EAPDocumentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    permission_class = [permissions.IsAuthenticated]
    serializer_class = EAPDocumentSerializer

    def get_queryset(self):
        return EAPDocument.objects.all()


class EAPViewSet(viewsets.ModelViewSet):
    serializer_class = EAPSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EAP.objects.all().order_by('-created_at')


class EAPStatusOptions(views.APIView):
    def get(self, request, format=None):
        options = {
            'eap_status': [
                {
                    'value': value,
                    'label': label,
                } for value, label in EAP.Status.choices
            ]
        }
        return Response(options)


class EarlyActionIndicatorOptions(views.APIView):
    def get(self, request, format=None):
        options = {
            'eap_status': [
                {
                    'value': value,
                    'label': label,
                } for value, label in EarlyActionIndicator.IndicatorChoices.choices
            ]
        }
        return Response(options)
