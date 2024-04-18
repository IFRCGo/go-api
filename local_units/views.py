from rest_framework import (
    viewsets,
    permissions,
    response
)
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView
)
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema

from .models import LocalUnit, DelegationOffice
from .serializers import LocalUnitSerializer, DelegationOfficeSerializer
from local_units.filterset import LocalUnitFilters, DelegationOfficeFilters
from local_units.models import (
    LocalUnit,
    LocalUnitLevel,
    LocalUnitType,
    Affiliation,
    Functionality,
    FacilityType,
    PrimaryHCC,
    HospitalType,
    BloodService,
    ProfessionalTrainingFacility,
)
from local_units.serializers import (
    LocalUnitSerializer,
    LocalUnitOptionsSerializer,
    LocalUnitDetailSerializer
)
from local_units.permissions import ValidateLocalUnitPermission


class LocalUnitViewSet(viewsets.ModelViewSet):
    queryset = LocalUnit.objects.all()
    serializer_class = LocalUnitSerializer
    filterset_class = LocalUnitFilters
    search_fields = ('local_branch_name', 'english_branch_name',)

    def get_serializer_class(self):
        if self.action == "list":
            return LocalUnitSerializer
        return LocalUnitDetailSerializer

    @extend_schema(
        request=None,
        responses=LocalUnitOptionsSerializer
    )
    @action(
        detail=False,
        url_path="options",
        methods=("get",),
        serializer_class=LocalUnitOptionsSerializer,
    )
    def get_options(self, request, pk=None):
        return response.Response(
            LocalUnitOptionsSerializer(
                instance=dict(
                    type=LocalUnitType.objects.all(),
                    level=LocalUnitLevel.objects.all(),
                    affiliation=Affiliation.objects.all(),
                    functionality=Functionality.objects.all(),
                    health_facility_type=FacilityType.objects.all(),
                    primary_health_care_center=PrimaryHCC.objects.all(),
                    hospital_type=HospitalType.objects.all(),
                    blood_services=BloodService.objects.all(),
                    professional_training_facilities=ProfessionalTrainingFacility.objects.all(),
                )
            ).data
        )

    @action(
        detail=True,
        url_path="validate",
        methods=["post"],
        serializer_class=LocalUnitSerializer,
        permission_classes=[permissions.IsAuthenticated, ValidateLocalUnitPermission]
    )
    def get_validate(self, request, pk=None, version=None):
        local_unit = self.get_object()
        local_unit.validated = True
        local_unit.save(update_fields=["validated"])
        serializer = LocalUnitSerializer(local_unit, context={"request": request})
        return response.Response(serializer.data)


class DelegationOfficeListAPIView(ListAPIView):
    queryset = DelegationOffice.objects.all()
    serializer_class = DelegationOfficeSerializer
    filterset_class = DelegationOfficeFilters
    search_fields = ('name', 'country__name')


class DelegationOfficeDetailAPIView(RetrieveAPIView):
    queryset = DelegationOffice.objects.all()
    serializer_class = DelegationOfficeSerializer
    permission_classes = [permissions.IsAuthenticated]
