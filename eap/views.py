# Create your views here.
from django.db.models import Case, F, IntegerField, Value, When
from django.db.models.query import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, permissions, response, status, viewsets
from rest_framework.decorators import action

from eap.filter_set import EAPRegistrationFilterSet, SimplifiedEAPFilterSet
from eap.models import EAPFile, EAPRegistration, EAPStatus, EAPType, SimplifiedEAP
from eap.permissions import (
    EAPBasePermission,
    EAPRegistrationPermissions,
    EAPValidatedBudgetPermission,
)
from eap.serializers import (
    EAPFileInputSerializer,
    EAPFileSerializer,
    EAPRegistrationSerializer,
    EAPStatusSerializer,
    EAPValidatedBudgetFileSerializer,
    MiniEAPSerializer,
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


class ActiveEAPViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = EAPRegistration.objects.all()
    lookup_field = "id"
    serializer_class = MiniEAPSerializer
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserPermission]
    filterset_class = EAPRegistrationFilterSet

    def get_queryset(self) -> QuerySet[EAPRegistration]:
        return (
            super()
            .get_queryset()
            .filter(status__in=[EAPStatus.APPROVED, EAPStatus.ACTIVATED])
            .select_related(
                "disaster_type",
                "country",
            )
            .annotate(
                requirement_cost=Case(
                    # TODO(susilnem): Verify the requirements(CHF) field map
                    When(
                        eap_type=EAPType.SIMPLIFIED_EAP,
                        then=SimplifiedEAP.objects.filter(eap_registration=F("id"))
                        .order_by("version")
                        .values("total_budget")[:1],
                    ),
                    # TODO(susilnem): Add check for FullEAP
                    # When(
                    #     eap_type=EAPType.FULL_EAP,
                    #     then=FullEAP.objects.filter(eap_registration=F("id")).order_by("version").values("total_budget")[:1],
                    # )
                    default=Value(0),
                    output_field=IntegerField(),
                )
            )
        )


class EAPRegistrationViewSet(EAPModelViewSet):
    queryset = EAPRegistration.objects.all()
    lookup_field = "id"
    serializer_class = EAPRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserMutationPermission, EAPRegistrationPermissions]
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
            .order_by("id")
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

    @action(
        detail=True,
        url_path="upload-validated-budget-file",
        methods=["post"],
        serializer_class=EAPValidatedBudgetFileSerializer,
        permission_classes=[permissions.IsAuthenticated, DenyGuestUserPermission, EAPValidatedBudgetPermission],
    )
    def upload_validated_budget_file(
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
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserMutationPermission, EAPBasePermission]

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

    @extend_schema(request=EAPFileInputSerializer, responses=EAPFileSerializer(many=True))
    @action(
        detail=False,
        url_path="multiple",
        methods=["POST"],
        permission_classes=[permissions.IsAuthenticated, DenyGuestUserPermission],
    )
    def multiple_file(self, request):
        files = [files[0] for files in dict((request.data).lists()).values()]
        data = [{"file": file} for file in files]
        file_serializer = EAPFileSerializer(data=data, context={"request": request}, many=True)
        if file_serializer.is_valid(raise_exception=True):
            file_serializer.save()
            return response.Response(file_serializer.data, status=status.HTTP_201_CREATED)
        return response.Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
