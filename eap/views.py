# Create your views here.

from rest_framework import (
    views,
    viewsets,
    response,
    permissions,
    mixins,
    status,
)
from rest_framework.decorators import action
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

    @action(
        detail=False,
        url_path='multiple',
        methods=['POST'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def multiple_file(self, request, pk=None, version=None):
        # converts querydict to original dict
        files = dict((request.data).lists())['file']
        data = [{'file': file} for file in files]
        file_serializer = EAPDocumentSerializer(data=data, context={'request': request}, many=True)
        if file_serializer.is_valid():
            file_serializer.save()
            return response.Response(file_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return response.Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EAPViewSet(viewsets.ModelViewSet):
    serializer_class = EAPSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # return EAP.objects.all()
        return EAP.objects.all().order_by(
            '-created_at'
        ).select_related(
            'country',
            'created_by',
            # 'modified_by',
            'disaster_type',
        ).prefetch_related(
            'districts',
            'documents',
            'early_actions',
            'early_actions__action',
            'early_actions__early_actions_prioritized_risk',
            'early_actions__indicators',
            'eap_reference',
            'eap_partner',
        )


class EAPActivationReportViewSet(viewsets.ModelViewSet):
    serializer_class = EAPActivationReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EAPActivationReport.objects.all().order_by(
            '-created_at'
        ).select_related(
            'created_by',
            'modified_by',
            'eap_activation',
            'ifrc_financial_report',
        ).prefetch_related(
            'documents',
            'operational_plans',
        )


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
