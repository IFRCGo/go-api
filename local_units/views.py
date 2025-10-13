from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Case, When
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, permissions, response, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView, RetrieveAPIView

from api.utils import bad_request
from local_units.filterset import (
    DelegationOfficeFilters,
    ExternallyManagedLocalUnitFilters,
    HealthLocalUnitFilters,
    LocalUnitBulkUploadFilters,
    LocalUnitFilters,
)
from local_units.models import (
    Affiliation,
    BloodService,
    DelegationOffice,
    ExternallyManagedLocalUnit,
    FacilityType,
    Functionality,
    GeneralMedicalService,
    HospitalType,
    LocalUnit,
    LocalUnitBulkUpload,
    LocalUnitChangeRequest,
    LocalUnitLevel,
    LocalUnitType,
    PrimaryHCC,
    ProfessionalTrainingFacility,
    SpecializedMedicalService,
    VisibilityChoices,
)
from local_units.permissions import (
    BulkUploadValidatorPermission,
    ExternallyManagedLocalUnitPermission,
    IsAuthenticatedForLocalUnit,
    ValidateLocalUnitPermission,
)
from local_units.serializers import (
    DelegationOfficeSerializer,
    ExternallyManagedLocalUnitSerializer,
    HealthLocalUnitFlatSerializer,
    LocalUnitBulkUploadSerializer,
    LocalUnitChangeRequestSerializer,
    LocalUnitDeprecateSerializer,
    LocalUnitDetailSerializer,
    LocalUnitOptionsSerializer,
    LocalUnitSerializer,
    LocalUnitTemplateFilesSerializer,
    PrivateLocalUnitDetailSerializer,
    PrivateLocalUnitSerializer,
    RejectedReasonSerialzier,
)
from local_units.tasks import (
    send_deprecate_email,
    send_local_unit_email,
    send_revert_email,
    send_validate_success_email,
)
from local_units.utils import get_user_validator_level
from main.permissions import DenyGuestUserPermission


class PrivateLocalUnitViewSet(viewsets.ModelViewSet):
    queryset = (
        LocalUnit.objects.select_related(
            "health",
            "country",
            "type",
            "level",
            "created_by",
            "modified_by",
            "health__health_facility_type",
        )
        .exclude(is_deprecated=True)
        .annotate(
            order=Case(
                When(status=LocalUnit.Status.PENDING_EDIT_VALIDATION, then=1),
                When(status=LocalUnit.Status.UNVALIDATED, then=2),
                When(status=LocalUnit.Status.VALIDATED, then=3),
                When(status=LocalUnit.Status.EXTERNALLY_MANAGED, then=4),
            )
        )
        .order_by("order", "-modified_at")
    )
    filterset_class = LocalUnitFilters
    search_fields = (
        "local_branch_name",
        "english_branch_name",
    )
    permission_classes = [permissions.IsAuthenticated, IsAuthenticatedForLocalUnit, DenyGuestUserPermission]

    def get_serializer_class(self):
        if self.action == "list":
            return PrivateLocalUnitSerializer
        return PrivateLocalUnitDetailSerializer

    def destroy(self, request, *args, **kwargs):
        return bad_request("Delete method not allowed")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Creating a new change request for the local unit
        LocalUnitChangeRequest.objects.create(
            local_unit=serializer.instance,
            status=LocalUnitChangeRequest.Status.PENDING,
            triggered_by=request.user,
        )
        transaction.on_commit(lambda: send_local_unit_email.delay(serializer.instance.id, new=True))
        return response.Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        local_unit = self.get_object()
        if local_unit.status != LocalUnit.Status.VALIDATED:
            return bad_request("Only validated local unit is allowed to update")
        update_reason = request.data.get("update_reason_overview")
        if not update_reason:
            raise ValidationError({"update_reason_overview": "Update reason is required."})

        # NOTE: Locking the local unit after the change request is created
        previous_data = PrivateLocalUnitDetailSerializer(local_unit, context={"request": request}).data
        local_unit.status = LocalUnit.Status.PENDING_EDIT_VALIDATION
        local_unit.update_reason_overview = update_reason
        local_unit.save(
            update_fields=[
                "status",
                "update_reason_overview",
            ]
        )
        serializer = self.get_serializer(local_unit, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        # Creating a new change request for the local unit
        LocalUnitChangeRequest.objects.create(
            local_unit=local_unit,
            previous_data=previous_data,
            status=LocalUnitChangeRequest.Status.PENDING,
            triggered_by=request.user,
        )
        transaction.on_commit(lambda: send_local_unit_email.delay(local_unit.id, new=False))
        return response.Response(serializer.data)

    @extend_schema(request=None, responses=PrivateLocalUnitSerializer)
    @action(
        detail=True,
        url_path="validate",
        methods=["post"],
        serializer_class=PrivateLocalUnitSerializer,
        permission_classes=[permissions.IsAuthenticated, ValidateLocalUnitPermission, DenyGuestUserPermission],
    )
    def get_validate(self, request, pk=None, version=None):
        local_unit = self.get_object()
        user = request.user
        # NOTE: Updating the change request with the approval status
        change_request_instance = LocalUnitChangeRequest.objects.filter(
            local_unit=local_unit,
            status=LocalUnitChangeRequest.Status.PENDING,
        ).last()
        if not change_request_instance:
            return response.Response(
                {"message": "No change request found to validate"},
                status=status.HTTP_404_NOT_FOUND,
            )

        validator = get_user_validator_level(user, local_unit)

        change_request_instance.current_validator = validator
        change_request_instance.status = LocalUnitChangeRequest.Status.APPROVED
        change_request_instance.updated_by = user
        change_request_instance.updated_at = timezone.now()
        change_request_instance.save(update_fields=["status", "updated_by", "updated_at", "current_validator"])

        # Validate the local unit
        local_unit.status = LocalUnit.Status.VALIDATED
        local_unit.save(
            update_fields=[
                "status",
            ]
        )
        serializer = PrivateLocalUnitSerializer(local_unit, context={"request": request})
        transaction.on_commit(lambda: send_validate_success_email.delay(local_unit_id=local_unit.id, message="Approved"))
        return response.Response(serializer.data)

    @extend_schema(request=RejectedReasonSerialzier, responses=PrivateLocalUnitDetailSerializer)
    @action(
        detail=True,
        url_path="revert",
        methods=["post"],
        serializer_class=RejectedReasonSerialzier,
        permission_classes=[permissions.IsAuthenticated, ValidateLocalUnitPermission, DenyGuestUserPermission],
    )
    def get_revert(self, request, pk=None, version=None):
        local_unit = self.get_object()

        if local_unit.status == LocalUnit.Status.VALIDATED:
            return bad_request("Local unit is already validated and cannot be reverted")

        rejected_data = PrivateLocalUnitDetailSerializer(local_unit, context={"request": request}).data

        serializer = RejectedReasonSerialzier(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data["reason"]

        # NOTE: Updating the change request with the rejection reason
        change_request_instance = LocalUnitChangeRequest.objects.filter(
            local_unit=local_unit,
            status=LocalUnitChangeRequest.Status.PENDING,
        ).last()

        if not change_request_instance:
            return response.Response(
                {"message": "No change request found to revert"},
                status=status.HTTP_404_NOT_FOUND,
            )

        change_request_instance.status = LocalUnitChangeRequest.Status.REVERT
        change_request_instance.rejected_reason = reason
        change_request_instance.updated_by = request.user
        change_request_instance.updated_at = timezone.now()
        change_request_instance.rejected_data = rejected_data
        change_request_instance.save(update_fields=["status", "rejected_reason", "updated_at", "updated_by", "rejected_data"])

        # NOTE: Handling the first change request
        if change_request_instance.previous_data == {}:
            total_change_request_count = LocalUnitChangeRequest.objects.filter(local_unit=local_unit).count()
            assert (
                total_change_request_count == 1
            ), f"There should be one change request and it is the first one {total_change_request_count}"
            local_unit.is_deprecated = True
            local_unit.deprecated_reason = LocalUnit.DeprecateReason.OTHER
            local_unit.deprecated_reason_overview = reason
            local_unit.save(
                update_fields=["is_deprecated", "deprecated_reason", "deprecated_reason_overview"],
            )
            return response.Response(PrivateLocalUnitDetailSerializer(local_unit, context={"request": request}).data)

        # NOTE: validating the reverted local unit
        local_unit.status = LocalUnit.Status.VALIDATED
        local_unit.save(update_fields=["status"])

        # reverting the previous data of change request to local unit by passing through serializer
        serializer = PrivateLocalUnitDetailSerializer(
            local_unit,
            data=change_request_instance.previous_data,
            context={"request": request},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        transaction.on_commit(
            lambda: send_revert_email.delay(local_unit_id=local_unit.id, change_request_id=change_request_instance.id)
        )
        return response.Response(serializer.data)

    @extend_schema(request=None, responses=LocalUnitChangeRequestSerializer)
    @action(
        detail=True,
        url_path="latest-change-request",
        methods=["get"],
        serializer_class=LocalUnitChangeRequestSerializer,
        permission_classes=[permissions.IsAuthenticated, DenyGuestUserPermission],
    )
    def get_latest_changes(self, request, pk=None, version=None):
        local_unit = self.get_object()

        change_request = LocalUnitChangeRequest.objects.filter(
            local_unit=local_unit,
        ).last()

        if not change_request:
            return response.Response(
                {"message": "Last change request not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = LocalUnitChangeRequestSerializer(change_request, context={"request": request})
        return response.Response(serializer.data)

    @extend_schema(request=LocalUnitDeprecateSerializer, responses=None)
    @action(
        detail=True,
        methods=["post"],
        url_path="deprecate",
        serializer_class=LocalUnitDeprecateSerializer,
        permission_classes=[permissions.IsAuthenticated, DenyGuestUserPermission, ValidateLocalUnitPermission],
    )
    def deprecate(self, request, pk=None):
        """Deprecate local unit object object"""
        instance = self.get_object()
        serializer = LocalUnitDeprecateSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        transaction.on_commit(lambda: send_deprecate_email.delay(instance.id))
        return response.Response(
            {"message": "Local unit object deprecated successfully."},
            status=status.HTTP_200_OK,
        )

    @extend_schema(request=None, responses=PrivateLocalUnitSerializer)
    @action(
        detail=True,
        methods=["post"],
        url_path="revert-deprecate",
        permission_classes=[permissions.IsAuthenticated, ValidateLocalUnitPermission, DenyGuestUserPermission],
    )
    def revert_deprecate(self, request, pk=None):
        """Revert the deprecate local unit object."""
        local_unit = get_object_or_404(LocalUnit, pk=pk)
        local_unit.is_deprecated = False
        local_unit.deprecated_reason = None
        local_unit.deprecated_reason_overview = ""
        local_unit.save(
            update_fields=[
                "is_deprecated",
                "deprecated_reason",
                "deprecated_reason_overview",
            ]
        )
        serializer = PrivateLocalUnitSerializer(local_unit, context={"request": request})
        return response.Response(serializer.data)


class LocalUnitViewSet(viewsets.ModelViewSet):
    queryset = LocalUnit.objects.select_related(
        "health",
        "country",
        "type",
        "level",
    ).filter(visibility=VisibilityChoices.PUBLIC, is_deprecated=False)
    filterset_class = LocalUnitFilters
    search_fields = (
        "local_branch_name",
        "english_branch_name",
    )

    def get_serializer_class(self):
        if self.action == "list":
            return LocalUnitSerializer
        return LocalUnitDetailSerializer

    def create(self, request, *args, **kwargs):
        return bad_request("Create method not allowed")

    def update(self, request, *args, **kwargs):
        return bad_request("Update method not allowed")

    def destroy(self, request, *args, **kwargs):
        return bad_request("Delete method not allowed")


class HealthLocalUnitViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public, flattened list of health local units (Type Code = 2).
    """

    serializer_class = HealthLocalUnitFlatSerializer
    http_method_names = ["get", "head", "options"]
    filterset_class = HealthLocalUnitFilters

    queryset = (
        LocalUnit.objects.select_related(
            "country",
            "type",
            "health",
            "health__affiliation",
            "health__functionality",
            "health__health_facility_type",
            "health__primary_health_care_center",
            "health__hospital_type",
        )
        .prefetch_related(
            "health__general_medical_services",
            "health__specialized_medical_beyond_primary_level",
            "health__blood_services",
            "health__professional_training_facilities",
        )
        .filter(
            visibility=VisibilityChoices.PUBLIC,
            is_deprecated=False,
            type__code=2,
            health__isnull=False,
        )
        .order_by("id")
    )

    # NOTE: Filters for region/country/iso/validated/subtype can be added later; base queryset enforces type=2.


class LocalUnitOptionsView(views.APIView):

    @extend_schema(request=None, responses=LocalUnitOptionsSerializer)
    def get(self, request, version=None):
        return response.Response(
            LocalUnitOptionsSerializer(
                dict(
                    type=LocalUnitType.objects.all(),
                    level=LocalUnitLevel.objects.all(),
                    affiliation=Affiliation.objects.all(),
                    functionality=Functionality.objects.all(),
                    health_facility_type=FacilityType.objects.all(),
                    primary_health_care_center=PrimaryHCC.objects.all(),
                    hospital_type=HospitalType.objects.all(),
                    blood_services=BloodService.objects.all(),
                    professional_training_facilities=ProfessionalTrainingFacility.objects.all(),
                    general_medical_services=GeneralMedicalService.objects.all(),
                    specialized_medical_beyond_primary_level=SpecializedMedicalService.objects.all(),
                ),
                context={"request": request},
            ).data
        )


class DelegationOfficeListAPIView(ListAPIView):
    queryset = DelegationOffice.objects.all()
    serializer_class = DelegationOfficeSerializer
    filterset_class = DelegationOfficeFilters
    search_fields = ("name", "country__name")


class DelegationOfficeDetailAPIView(RetrieveAPIView):
    queryset = DelegationOffice.objects.all()
    serializer_class = DelegationOfficeSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        DenyGuestUserPermission,
    ]


class ExternallyManagedLocalUnitViewSet(
    mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    queryset = ExternallyManagedLocalUnit.objects.select_related("country", "local_unit_type")
    serializer_class = ExternallyManagedLocalUnitSerializer
    filterset_class = ExternallyManagedLocalUnitFilters
    permission_classes = [permissions.IsAuthenticated, ExternallyManagedLocalUnitPermission]


class LocalUnitBulkUploadViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = LocalUnitBulkUpload.objects.select_related("country", "local_unit_type", "triggered_by").order_by("-triggered_at")
    permission_classes = [
        permissions.IsAuthenticated,
        DenyGuestUserPermission,
        BulkUploadValidatorPermission,
    ]
    serializer_class = LocalUnitBulkUploadSerializer
    filterset_class = LocalUnitBulkUploadFilters

    @extend_schema(
        request=None,
        responses=LocalUnitTemplateFilesSerializer,
        parameters=[
            OpenApiParameter(
                name="bulk_upload_template",
                description="Type of template for local unit or local unit health care bulk upload",
                required=False,
                type=str,
                enum=["local_unit", "health_care"],
            )
        ],
    )
    @action(detail=False, methods=["get"], url_path="get-bulk-upload-template")
    def get_bulk_upload_template(self, request):
        template_type = request.query_params.get("bulk_upload_template", "local_unit")
        if template_type == "health_care":
            file_url = request.build_absolute_uri(static("files/local_units/Health Care Bulk Import Template - Local Units.xlsx"))
        else:
            file_url = request.build_absolute_uri(
                static("files/local_units/Administrative Bulk Import Template - Local Units.xlsx")
            )
        template = {"template_url": file_url}
        return response.Response(LocalUnitTemplateFilesSerializer(template).data)
