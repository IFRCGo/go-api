# Create your views here.

from rest_framework import (
    views,
    viewsets,
    response,
    permissions,
    mixins,
)
from .models import (
    EarlyActionIndicator,
    EAP,
    EAPDocument,
    EarlyAction,
    EAPActivationReport,
)
from .serializers import (
    EAPSerializer,
    EAPDocumentSerializer,
    EAPActivationReportSerializer,
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


class EAPActivationReportViewSet(viewsets.ModelViewSet):
    serializer_class = EAPActivationReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EAPActivationReport.objects.all().order_by('-created_at')


class EAPOptionsView(views.APIView):
    """
    Options for various attribute related to eap
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, version=None):
        options = {
            "status": [
                {
                    "key": status.value,
                    "value": status.label
                } for status in EAP.Status
            ],
            "early_actions_indicators": [
                {
                    "key": indicator.value,
                    "value": indicator.label
                } for indicator in EarlyActionIndicator.IndicatorChoices
            ],
            "sectors": [
                {
                    "key": sector.value,
                    "value": sector.label
                } for sector in EarlyAction.Sector
            ],
        }
        return response.Response(options)
