from django.contrib.auth.models import Permission
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, response, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView, RetrieveAPIView

from api.utils import bad_request
from local_units.filterset import DelegationOfficeFilters, LocalUnitFilters
from local_units.models import (
    Affiliation,
    BloodService,
    DelegationOffice,
    FacilityType,
    Functionality,
    GeneralMedicalService,
    HospitalType,
    LocalUnit,
    LocalUnitChangeRequest,
    LocalUnitLevel,
    LocalUnitType,
    PrimaryHCC,
    ProfessionalTrainingFacility,
    SpecializedMedicalService,
    VisibilityChoices,
)
from local_units.permissions import (
    IsAuthenticatedForLocalUnit,
    ValidateLocalUnitPermission,
)
from local_units.serializers import (
    DelegationOfficeSerializer,
    LocalUnitChangeRequestSerializer,
    LocalUnitDeprecateSerializer,
    LocalUnitDetailSerializer,
    LocalUnitOptionsSerializer,
    LocalUnitSerializer,
    PrivateLocalUnitDetailSerializer,
    PrivateLocalUnitSerializer,
    RejectedReasonSerialzier,
)
from main.permissions import DenyGuestUserPermission


class PrivateLocalUnitViewSet(viewsets.ModelViewSet):
    queryset = LocalUnit.objects.select_related(
        "health",
        "country",
        "type",
        "level",
    ).exclude(is_deprecated=True)
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
            previous_data=serializer.data,
            status=LocalUnitChangeRequest.Status.PENDING,
            triggered_by=request.user,
        )
        return response.Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        local_unit = self.get_object()

        # NOTE: Checking if the local unit is locked.
        # TODO: This should be moved to a permission class and validators can update the local unit
        if local_unit.is_locked:
            return bad_request("Local unit is locked and cannot be updated")

        # NOTE: Locking the local unit after the change request is created
        local_unit.is_locked = True
        serializer = self.get_serializer(local_unit, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Creating a new change request for the local unit
        LocalUnitChangeRequest.objects.create(
            local_unit=local_unit,
            previous_data=serializer.data,
            status=LocalUnitChangeRequest.Status.PENDING,
            triggered_by=request.user,
        )
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

        # NOTE: Updating the change request with the approval status
        change_request_instance = LocalUnitChangeRequest.objects.filter(
            local_unit=local_unit,
            status=LocalUnitChangeRequest.Status.PENDING,
        ).last()

        if not change_request_instance:
            return bad_request("No change request found to validate")

        # Checking the validator type

        validator = LocalUnitChangeRequest.Validator.LOCAL
        if request.user.is_superuser or request.user.has_perm("local_units.local_unit_global_validator"):
            validator = LocalUnitChangeRequest.Validator.GLOBAL
        else:
            region_admin_ids = [
                int(codename.replace("region_admin_", ""))
                for codename in Permission.objects.filter(
                    group__user=request.user,
                    codename__startswith="region_admin_",
                ).values_list("codename", flat=True)
            ]
            if local_unit.country.region_id in region_admin_ids:
                validator = LocalUnitChangeRequest.Validator.REGIONAL

        change_request_instance.current_validator = validator
        change_request_instance.status = LocalUnitChangeRequest.Status.APPROVED
        change_request_instance.updated_by = request.user
        change_request_instance.updated_at = timezone.now()
        change_request_instance.save(update_fields=["status", "updated_by", "updated_at", "current_validator"])

        # Validate the local unit
        local_unit.validated = True
        local_unit.is_locked = False
        local_unit.save(update_fields=["validated", "is_locked"])
        serializer = PrivateLocalUnitSerializer(local_unit, context={"request": request})
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

        if local_unit.validated:
            return bad_request("Local unit is already validated and cannot be reverted")

        full_serializer = PrivateLocalUnitDetailSerializer(local_unit, context={"request": request})

        serializer = RejectedReasonSerialzier(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data["reason"]

        # NOTE: Updating the change request with the rejection reason
        change_request_instance = LocalUnitChangeRequest.objects.filter(
            local_unit=local_unit,
            status=LocalUnitChangeRequest.Status.PENDING,
        ).last()

        if not change_request_instance:
            return bad_request("No change request found to revert")

        change_request_instance.status = LocalUnitChangeRequest.Status.REVERT
        change_request_instance.rejected_reason = reason
        change_request_instance.updated_by = request.user
        change_request_instance.updated_at = timezone.now()
        change_request_instance.rejected_data = full_serializer.data
        change_request_instance.save(update_fields=["status", "rejected_reason", "updated_at", "updated_by", "rejected_data"])

        # Reverting the last change request related to this local unit
        last_change_request = LocalUnitChangeRequest.objects.filter(
            local_unit=local_unit,
            status=LocalUnitChangeRequest.Status.APPROVED,
        ).last()

        if not last_change_request:
            return bad_request("No change request found to revert")

        # NOTE: Unlocking the reverted local unit
        local_unit.is_locked = False
        local_unit.save(update_fields=["is_locked"])

        # reverting the previous data of change request to local unit by passing through serializer
        serializer = PrivateLocalUnitDetailSerializer(
            local_unit,
            data=last_change_request.previous_data,
            context={"request": request},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return response.Response(serializer.data)

    @extend_schema(request=None, responses=LocalUnitChangeRequestSerializer)
    @action(
        detail=True,
        url_path="latest-change-request",
        methods=["post"],
        serializer_class=LocalUnitChangeRequestSerializer,
        permission_classes=[permissions.IsAuthenticated, IsAuthenticatedForLocalUnit, DenyGuestUserPermission],
    )
    def get_latest_changes(self, request, pk=None, version=None):
        local_unit = self.get_object()

        change_request = LocalUnitChangeRequest.objects.filter(
            local_unit=local_unit,
            status=LocalUnitChangeRequest.Status.APPROVED,
        ).last()

        if not change_request:
            return bad_request("Last change request not found")

        serializer = LocalUnitChangeRequestSerializer(change_request, context={"request": request})
        return response.Response(serializer.data)

    @extend_schema(request=LocalUnitDeprecateSerializer, responses=None)
    @action(
        detail=True,
        methods=["post"],
        url_path="deprecate",
        serializer_class=LocalUnitDeprecateSerializer,
        permission_classes=[permissions.IsAuthenticated, DenyGuestUserPermission],
    )
    def deprecate(self, request, pk=None):
        """Deprecate local unit object object"""
        instance = self.get_object()
        serializer = LocalUnitDeprecateSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
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
        local_unit.save(update_fields=["is_deprecated", "deprecated_reason", "deprecated_reason_overview"])
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
