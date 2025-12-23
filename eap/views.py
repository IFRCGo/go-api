# Create your views here.
from django.db.models import Case, F, IntegerField, When
from django.db.models.query import Prefetch, QuerySet
from django.templatetags.static import static
from drf_spectacular.utils import OpenApiParameter, extend_schema
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
    EnableApproach,
    FullEAP,
    KeyActor,
    PlannedOperation,
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
    EAPTemplateFilesSerializer,
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
        return (
            super()
            .get_queryset()
            .filter(status__in=[EAPStatus.APPROVED, EAPStatus.ACTIVATED])
            .select_related("disaster_type", "country")
            .annotate(
                requirement_cost=Case(
                    When(
                        eap_type=EAPType.SIMPLIFIED_EAP,
                        then=F("latest_simplified_eap__total_budget"),
                    ),
                    When(
                        eap_type=EAPType.FULL_EAP,
                        then=F("latest_full_eap__total_budget"),
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
                "cover_image__created_by",
                "cover_image__modified_by",
                "budget_file__created_by",
                "budget_file__modified_by",
                "eap_registration__country",
                "eap_registration__disaster_type",
            )
            .prefetch_related(
                "eap_registration__partners",
                "admin2",
                Prefetch(
                    "planned_operations",
                    queryset=PlannedOperation.objects.prefetch_related(
                        "indicators",
                        "readiness_activities",
                        "prepositioning_activities",
                        "early_action_activities",
                    ),
                ),
                Prefetch(
                    "enable_approaches",
                    queryset=EnableApproach.objects.prefetch_related(
                        "indicators",
                        "readiness_activities",
                        "prepositioning_activities",
                        "early_action_activities",
                    ),
                ),
                Prefetch(
                    "hazard_impact_images",
                    queryset=EAPFile.objects.select_related("created_by", "modified_by"),
                ),
                Prefetch(
                    "risk_selected_protocols_images",
                    queryset=EAPFile.objects.select_related("created_by", "modified_by"),
                ),
                Prefetch(
                    "selected_early_actions_images",
                    queryset=EAPFile.objects.select_related("created_by", "modified_by"),
                ),
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
                "budget_file",
            )
            .prefetch_related(
                "admin2",
                "prioritized_impacts",
                "early_actions",
                # source information
                "risk_analysis_source_of_information",
                "trigger_statement_source_of_information",
                "trigger_model_source_of_information",
                "evidence_base_source_of_information",
                "activation_process_source_of_information",
                # Files
                "hazard_selection_images",
                "theory_of_change_table_file",
                "exposed_element_and_vulnerability_factor_images",
                "prioritized_impact_images",
                "risk_analysis_relevant_files",
                "forecast_selection_images",
                "definition_and_justification_impact_level_images",
                "identification_of_the_intervention_area_images",
                "trigger_model_relevant_files",
                "early_action_selection_process_images",
                "evidence_base_relevant_files",
                "early_action_implementation_images",
                "trigger_activation_system_images",
                "activation_process_relevant_files",
                "meal_relevant_files",
                "capacity_relevant_files",
                "forecast_table_file",
                Prefetch(
                    "key_actors",
                    queryset=KeyActor.objects.select_related("national_society"),
                ),
                Prefetch(
                    "planned_operations",
                    queryset=PlannedOperation.objects.prefetch_related(
                        "indicators",
                        "readiness_activities",
                        "prepositioning_activities",
                        "early_action_activities",
                    ),
                ),
                Prefetch(
                    "enable_approaches",
                    queryset=EnableApproach.objects.prefetch_related(
                        "indicators",
                        "readiness_activities",
                        "prepositioning_activities",
                        "early_action_activities",
                    ),
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

    @extend_schema(
        request=None,
        responses=EAPTemplateFilesSerializer,
        parameters=[
            OpenApiParameter(
                name="get_template_files",
                description="Type of template to download",
                required=False,
                type=str,
                enum=[
                    "eap_budget",
                    "full_eap_forecast_table",
                    "full_eap_theory_of_change_table",
                ],
            )
        ],
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="get-template-files",
        permission_classes=[permissions.IsAuthenticated, DenyGuestUserPermission],
    )
    def get_template_files(self, request):
        template_type = request.query_params.get("get_template_files")

        template_map = {
            "eap_budget": "files/eap/eap_budget_template.xlsm",
            "full_eap_forecast_table": "files/eap/full_eap_forecasts_table.docx",
            "full_eap_theory_of_change_table": "files/eap/full_eap_theory_of_change_table.docx",
        }

        if not template_type:
            return response.Response(
                {
                    "detail": "Please provide a template type.",
                    "available_types": list(template_map.keys()),
                },
                status=400,
            )
        if template_type not in template_map:
            return response.Response(
                {
                    "detail": f"Invalid template type '{template_type}'.",
                    "available_types": list(template_map.keys()),
                },
                status=400,
            )
        file_url = request.build_absolute_uri(static(template_map[template_type]))
        return response.Response({"template_url": file_url})
