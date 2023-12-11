from rest_framework import (
    viewsets,
    permissions,
    response
)
from rest_framework.decorators import action


from .models import LocalUnit, DelegationOffice
from .serializers import LocalUnitSerializer, DelegationOfficeSerializer
from local_units.filterset import LocalUnitFilters
from local_units.models import (
    LocalUnit,
    LocalUnitLevel,
    LocalUnitType,
)
from local_units.serializers import (
    LocalUnitSerializer,
    LocalUnitOptionsSerializer
)


class LocalUnitViewSet(viewsets.ModelViewSet):
    queryset = LocalUnit.objects.all()
    serializer_class = LocalUnitSerializer
    filterset_class = LocalUnitFilters
    search_fields = ('local_branch_name', 'english_branch_name',)


class LocalUnitDetailAPIView(RetrieveAPIView):
    queryset = LocalUnit.objects.all()
    serializer_class = LocalUnitSerializer


class DelegationOfficeFilters(filters.FilterSet):
    class Meta:
        model = DelegationOffice
        fields = (
            'country__name',
            'country__iso3',
            'country__iso',
            'dotype__code',
        )


class DelegationOfficeListAPIView(ListAPIView):
    queryset = DelegationOffice.objects.all()
    serializer_class = DelegationOfficeSerializer
    filterset_class = DelegationOfficeFilters
    search_fields = ('name', 'country__name')


class DelegationOfficeDetailAPIView(RetrieveAPIView):
    queryset = DelegationOffice.objects.all()
    serializer_class = DelegationOfficeSerializer
    permission_classes = [permissions.IsAuthenticated]

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
                )
            ).data
        )
