# Create your views here.
from django.db.models import Case, IntegerField, Subquery, When
from django.db.models.expressions import OuterRef
from django.db.models.query import Prefetch, QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, permissions, response, status, viewsets
from rest_framework.decorators import action

from eap.filter_set import (
    EAPRegistrationFilterSet,
    FullEAPFilterSet,
    SimplifiedEAPFilterSet,
)
from eap.models import (
    EAPFile,
    EAPRegistration,
    EAPStatus,
    EAPType,
    FullEAP,
    KeyActor,
    SimplifiedEAP,
)
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
    FullEAPSerializer,
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
        latest_simplified_eap = (
            SimplifiedEAP.objects.filter(eap_registration=OuterRef("id"), is_locked=False)
            .order_by("-version")
            .values("total_budget")[:1]
        )

        latest_full_eap = (
            FullEAP.objects.filter(eap_registration=OuterRef("id"), is_locked=False)
            .order_by("-version")
            .values("total_budget")[:1]
        )

        return (
            super()
            .get_queryset()
            .filter(status__in=[EAPStatus.APPROVED, EAPStatus.ACTIVATED])
            .select_related("disaster_type", "country")
            .annotate(
                requirement_cost=Case(
                    When(
                        eap_type=EAPType.SIMPLIFIED_EAP,
                        then=Subquery(latest_simplified_eap),
                    ),
                    When(
                        eap_type=EAPType.FULL_EAP,
                        then=Subquery(latest_full_eap),
                    ),
                    output_field=IntegerField(),
                )
            )
        )


class EAPRegistrationViewSet(EAPModelViewSet):
    queryset = EAPRegistration.objects.all()
    lookup_field = "id"
    serializer_class = EAPRegistrationSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        DenyGuestUserMutationPermission,
        EAPRegistrationPermissions,
    ]
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
        permission_classes=[
            permissions.IsAuthenticated,
            DenyGuestUserPermission,
            EAPValidatedBudgetPermission,
        ],
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
    permission_classes = [
        permissions.IsAuthenticated,
        DenyGuestUserMutationPermission,
        EAPBasePermission,
    ]

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
                "hazard_impact_images",
                "risk_selected_protocols_images",
                "selected_early_actions_images",
                "planned_operations",
                "enable_approaches",
            )
        )


class FullEAPViewSet(EAPModelViewSet):
    queryset = FullEAP.objects.all()
    lookup_field = "id"
    serializer_class = FullEAPSerializer
    filterset_class = FullEAPFilterSet
    permission_classes = [
        permissions.IsAuthenticated,
        DenyGuestUserMutationPermission,
        EAPBasePermission,
    ]

    def get_queryset(self) -> QuerySet[FullEAP]:
        return (
            super()
            .get_queryset()
            .select_related(
                "created_by",
                "modified_by",
            )
            .prefetch_related(
                "admin2",
                # source information
                "risk_analysis_source_of_information",
                "trigger_statement_source_of_information",
                "trigger_model_source_of_information",
                "evidence_base_source_of_information",
                "activation_process_source_of_information",
                # Files
                "hazard_selection_files",
                "theory_of_change_table_file",
                "exposed_element_and_vulnerability_factor_files",
                "prioritized_impact_files",
                "risk_analysis_relevant_files",
                "forecast_selection_files",
                "definition_and_justification_impact_level_files",
                "identification_of_the_intervention_area_files",
                "trigger_model_relevant_files",
                "early_action_selection_process_files",
                "evidence_base_files",
                "early_action_implementation_files",
                "trigger_activation_system_files",
                "activation_process_relevant_files",
                "meal_relevant_files",
                "capacity_relevant_files",
                Prefetch(
                    "key_actors",
                    queryset=KeyActor.objects.select_related("national_society"),
                ),
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
