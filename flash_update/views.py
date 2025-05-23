from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import (
    mixins,
    permissions,
    response,
    serializers,
    status,
    views,
    viewsets,
)
from rest_framework.decorators import action
from rest_framework.response import Response

from api.serializers import ActionSerializer
from main.permissions import DenyGuestUserPermission

from .filter_set import FlashUpdateFilter
from .models import (
    DonorGroup,
    Donors,
    FlashAction,
    FlashGraphicMap,
    FlashUpdate,
    FlashUpdateShare,
)
from .serializers import (
    DonorGroupSerializer,
    DonorsSerializer,
    ExportFlashUpdateViewSerializer,
    FlashGraphicMapFileInputSerializer,
    FlashGraphicMapSerializer,
    FlashUpdateSerializer,
    ShareFlashUpdateSerializer,
)
from .tasks import export_to_pdf


class FlashUpdateViewSet(viewsets.ModelViewSet):
    serializer_class = FlashUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserPermission]
    filterset_class = FlashUpdateFilter

    def get_queryset(self):
        return (
            FlashUpdate.objects.all()
            .select_related(
                "hazard_type",
                "created_by",
                "modified_by",
            )
            .prefetch_related(
                "references",
                "references__document",
                "map",
                "map__created_by",
                "graphics",
                "graphics__created_by",
                "actions_taken_flash__flash_update",
                "actions_taken_flash__actions",
                "flash_country_district__flash_update",
                "flash_country_district__country",
                "flash_country_district__district",
            )
            .order_by("-created_at")
            .distinct()
        )


class FlashUpdateFileViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserPermission]
    serializer_class = FlashGraphicMapSerializer

    def get_queryset(self):
        return FlashGraphicMap.objects.all().select_related("created_by")

    @extend_schema(request=FlashGraphicMapFileInputSerializer, responses=FlashGraphicMapSerializer(many=True))
    @action(
        detail=False,
        url_path="multiple",
        methods=["POST"],
        permission_classes=[permissions.IsAuthenticated, DenyGuestUserPermission],
    )
    def multiple_file(self, request, pk=None, version=None):
        files = [files[0] for files in dict((request.data).lists()).values()]
        data = [{"file": file} for file in files]
        if len(data) > 3:
            raise serializers.ValidationError("Number of files selected should not be greater than 3")
        file_serializer = FlashGraphicMapSerializer(data=data, context={"request": request}, many=True)
        if file_serializer.is_valid():
            file_serializer.save()
            return response.Response(file_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return response.Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FlashActionViewset(viewsets.ReadOnlyModelViewSet):
    queryset = FlashAction.objects.exclude(is_disabled=True)
    serializer_class = ActionSerializer
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserPermission]


class DonorGroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DonorGroup.objects.all()
    serializer_class = DonorGroupSerializer
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserPermission]


class DonorsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Donors.objects.all()
    serializer_class = DonorsSerializer
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserPermission]


class ShareFlashUpdateViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = FlashUpdateShare.objects.all()
    serializer_class = ShareFlashUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserPermission]


class ExportFlashUpdateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserPermission]

    @extend_schema(request=None, responses=ExportFlashUpdateViewSerializer)
    def get(self, request, pk, format=None):
        flash_update = get_object_or_404(FlashUpdate, pk=pk)
        if flash_update.extracted_file and flash_update.modified_at < flash_update.extracted_at:
            return Response(
                ExportFlashUpdateViewSerializer(
                    dict(status="ready", url=request.build_absolute_uri(flash_update.extracted_file.url))
                ).data
            )
        else:
            transaction.on_commit(lambda: export_to_pdf.delay(flash_update.id))
            return Response(ExportFlashUpdateViewSerializer(dict(status="pending", url=None)).data)
