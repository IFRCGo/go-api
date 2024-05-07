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
    VisibilityChoices,
    GeneralMedicalService,
    SpecializedMedicalService,
    DelegationOffice,
)
from local_units.serializers import (
    LocalUnitSerializer,
    LocalUnitOptionsSerializer,
    LocalUnitDetailSerializer,
    DelegationOfficeSerializer,
    PrivateLocalUnitSerializer,
    PrivateLocalUnitDetailSerializer
)
from local_units.permissions import (
    ValidateLocalUnitPermission,
    IsAuthenticatedForLocalUnit
)
from api.utils import bad_request


class LocalUnitViewSet(viewsets.ModelViewSet):
    queryset = LocalUnit.objects.select_related(
        'health',
        'country',
        'type',
        'level',
    )
    filterset_class = LocalUnitFilters
    search_fields = ('local_branch_name', 'english_branch_name',)
    permission_classes = [IsAuthenticatedForLocalUnit]

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_authenticated:
            return qs.filter(visibility=VisibilityChoices.PUBLIC)
        return qs

    def get_serializer_class(self):
        if self.action == "list" and self.request.user.id:
            return PrivateLocalUnitSerializer
            print
        elif self.action == "list":
            return LocalUnitSerializer
        elif self.action in ['create', 'retrieve', 'update', 'destroy'] and self.request.user.is_authenticated:
            return PrivateLocalUnitDetailSerializer
        return LocalUnitDetailSerializer

    def destroy(self, request, *args, **kwargs):
        return bad_request('Delete method not allowed')

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
                    general_medical_services=GeneralMedicalService.objects.all(),
                    specialized_medical_services=SpecializedMedicalService.objects.all(),
                ), context={'request': request}
            ).data
        )

    @extend_schema(
        responses=LocalUnitDetailSerializer
    )
    @action(
        detail=True,
        url_path="validate",
        methods=["post"],
        serializer_class=LocalUnitDetailSerializer,
        permission_classes=[permissions.IsAuthenticated, ValidateLocalUnitPermission]
    )
    def get_validate(self, request, pk=None, version=None):
        local_unit = self.get_object()
        local_unit.validated = True
        local_unit.save(update_fields=["validated"])
        serializer = LocalUnitDetailSerializer(local_unit, context={"request": request})
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
