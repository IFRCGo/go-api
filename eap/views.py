# Create your views here.
from django.db.models.query import QuerySet
from rest_framework import mixins, permissions, response, viewsets
from rest_framework.decorators import action

from eap.filter_set import EAPRegistrationFilterSet
from eap.models import EAPFile, EAPRegistration, SimplifiedEAP
from eap.serializers import (
    EAPFileSerializer,
    EAPRegistrationSerializer,
    EAPStatusSerializer,
    SimplifiedEAPSerializer,
)
from main.permissions import DenyGuestUserMutationPermission, DenyGuestUserPermission


class EAPRegistrationViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.CreateModelMixin,
):
    queryset = EAPRegistration.objects.all()
    serializer_class = EAPRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserMutationPermission]
    filterset_class = EAPRegistrationFilterSet

    def get_queryset(self) -> QuerySet[EAPRegistration]:
        return (
            super()
            .get_queryset()
            .select_related(
                "created_by",
                "modified_by",
                "national_society",
                "disaster_type",
            )
            .prefetch_related(
                "partners",
            )
        )

    @action(
        detail=True,
        url_path="status",
        methods=["post"],
        serializer_class=EAPStatusSerializer,
        permission_classes=[permissions.IsAuthenticated, DenyGuestUserPermission],
    )
    def update_status(
        self,
        request,
        pk: int | None = None,
    ):
        eap_registration = self.get_object()
        serializer = self.get_serializer(
            eap_registration,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data)


class SimplifiedEAPViewSet(viewsets.ModelViewSet):
    queryset = SimplifiedEAP.objects.all()
    serializer_class = SimplifiedEAPSerializer
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserMutationPermission]

    def get_queryset(self) -> QuerySet[SimplifiedEAP]:
        return (
            super()
            .get_queryset()
            .select_related(
                "created_by",
                "modified_by",
                "cover_image",
            )
            .prefetch_related(
                "eap_registration", "admin2", "hazard_impact_file", "selected_early_actions_file", "risk_selected_protocols_file"
            )
        )


class EAPFileViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
):
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserPermission]
    serializer_class = EAPFileSerializer

    def get_queryset(self) -> QuerySet[EAPFile]:
        if self.request is None:
            return EAPFile.objects.none()
        return EAPFile.objects.filter(created_by=self.request.user)
