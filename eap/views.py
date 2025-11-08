# Create your views here.
from django.db.models.query import QuerySet
from rest_framework import mixins, permissions, response, viewsets
from rest_framework.decorators import action

from eap.filter_set import EAPRegistrationFilterSet, SimplifiedEAPFilterSet
from eap.models import EAPFile, EAPRegistration, SimplifiedEAP
from eap.serializers import (
    EAPFileSerializer,
    EAPRegistrationSerializer,
    EAPStatusSerializer,
    SimplifiedEAPSerializer,
)
from main.permissions import DenyGuestUserMutationPermission, DenyGuestUserPermission


class EAPModelViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
):
    pass


class EAPRegistrationViewSet(EAPModelViewSet):
    queryset = EAPRegistration.objects.all()
    lookup_field = "id"
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
                "country",
            )
            .prefetch_related(
                "partners",
                "simplified_eap",
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
        id: int,
    ):
        eap_registration = self.get_object()
        serializer = self.get_serializer(
            eap_registration,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data)


class SimplifiedEAPViewSet(EAPModelViewSet):
    queryset = SimplifiedEAP.objects.all()
    lookup_field = "id"
    serializer_class = SimplifiedEAPSerializer
    filterset_class = SimplifiedEAPFilterSet
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserMutationPermission]

    def get_queryset(self) -> QuerySet[SimplifiedEAP]:
        return (
            super()
            .get_queryset()
            .select_related(
                "created_by",
                "modified_by",
                "cover_image",
                "eap_registration__country",
                "eap_registration__disaster_type",
            )
            .prefetch_related(
                "eap_registration__partners",
                "admin2",
                "hazard_impact_file",
                "selected_early_actions_file",
                "risk_selected_protocols_file",
                "selected_early_actions_file",
                "planned_operations",
                "enable_approaches",
            )
        )


class EAPFileViewSet(
    viewsets.GenericViewSet,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
):
    queryset = EAPFile.objects.all()
    lookup_field = "id"
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserPermission]
    serializer_class = EAPFileSerializer

    def get_queryset(self) -> QuerySet[EAPFile]:
        if self.request is None:
            return EAPFile.objects.none()
        return EAPFile.objects.filter(
            created_by=self.request.user,
        ).select_related(
            "created_by",
            "modified_by",
        )
