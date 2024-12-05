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
    FullLocalUnitSerializer,
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
        clean_data = FullLocalUnitSerializer(serializer.instance).data
        LocalUnitChangeRequest.objects.create(
            local_unit=serializer.instance,
            previous_data=clean_data,
            status=LocalUnitChangeRequest.Status.PENDING,
            triggered_by=request.user,
        )
        return response.Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        local_unit = self.get_object()

        # NOTE: Checking if the local unit is locked.
        if local_unit.is_locked:
            return bad_request("Local unit is locked and cannot be updated")

        clean_data = FullLocalUnitSerializer(local_unit).data

        # Creating a new change request for the local unit
        LocalUnitChangeRequest.objects.create(
            local_unit=local_unit,
            previous_data=clean_data,
            status=LocalUnitChangeRequest.Status.PENDING,
            triggered_by=request.user,
        )
        # NOTE: Locking the local unit after the change request is created
        local_unit.is_locked = True
        local_unit.save(update_fields=["is_locked"])
        return super().update(request, *args, **kwargs)

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

        clean_data = FullLocalUnitSerializer(local_unit).data

        # Creating a new change request to revert the local unit
        LocalUnitChangeRequest.objects.create(
            local_unit=local_unit,
            previous_data=clean_data,
            status=LocalUnitChangeRequest.Status.APPROVED,
            triggered_by=request.user,
            updated_by=request.user,
            updated_at=timezone.now(),
        )

        # Validate the local unit
        local_unit.validated = True
        local_unit.is_locked = False
        local_unit.save(update_fields=["validated", "is_locked"])
        serializer = PrivateLocalUnitSerializer(local_unit, context={"request": request})
        return response.Response(serializer.data)

    @extend_schema(request=RejectedReasonSerialzier, responses=PrivateLocalUnitSerializer)
    @action(
        detail=True,
        url_path="revert",
        methods=["post"],
        serializer_class=RejectedReasonSerialzier,
    )
    def get_revert(self, request, pk=None, version=None):
        local_unit = self.get_object()

        if local_unit.validated:
            return bad_request("Local unit is already validated and cannot be reverted")

        clean_data = FullLocalUnitSerializer(local_unit).data

        serializer = RejectedReasonSerialzier(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data["reason"]

        LocalUnitChangeRequest.objects.create(
            local_unit=local_unit,
            previous_data=clean_data,
            rejected_reason=reason,
            status=LocalUnitChangeRequest.Status.REVERT,
            triggered_by=request.user,
        )

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
        serializer = PrivateLocalUnitSerializer(
            local_unit,
            data=last_change_request.previous_data,
            context={"request": request},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return response.Response(serializer.data)

    @extend_schema(request=None, responses=PrivateLocalUnitDetailSerializer)
    @action(
        detail=True,
        url_path="latest-changes",
        methods=["post"],
        serializer_class=PrivateLocalUnitDetailSerializer,
    )
    def get_latest_changes(self, request, pk=None, version=None):
        local_unit = self.get_object()

        change_request = LocalUnitChangeRequest.objects.filter(
            local_unit=local_unit,
            status=LocalUnitChangeRequest.Status.APPROVED,
        ).last()

        if not change_request:
            return bad_request("Last change request not found")

        serializer = PrivateLocalUnitDetailSerializer(
            local_unit,
            data=change_request.previous_data,
            context={"request": request},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
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
                    specialized_medical_services=SpecializedMedicalService.objects.all(),
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
