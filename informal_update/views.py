from rest_framework.response import Response
from rest_framework import (
    views,
    viewsets,
    permissions,
    mixins
)

from django_filters import rest_framework as filters

from informal_update.models import (
    InformalUpdate,
    InformalGraphicMap,
    InformalAction
)

from informal_update.serializers import (
    InformalUpdateSerializer,
    InformalGraphicMapSerializer
)

from api.serializers import ActionSerializer


class InformalUpdateFilter(filters.FilterSet):
    hazayd_type = filters.NumberFilter(field_name='hazard_type', lookup_expr='exact')

    class Meta:
        model = InformalUpdate
        fields = {
            'created_at': ('exact', 'gt', 'gte', 'lt', 'lte'),
        }


class InformalUpdateViewSet(viewsets.ModelViewSet):
    serializer_class = InformalUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = InformalUpdateFilter

    def get_queryset(self):
        return InformalUpdate.objects.filter(
            created_by=self.request.user
        ).order_by('-created_at').distinct()


class InformalUpdateFileViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    permission_class = [permissions.IsAuthenticated]
    serializer_class = InformalGraphicMapSerializer

    def get_queryset(self):
        return InformalGraphicMap.objects.filter(created_by=self.request.user)


class InformalActionViewset(viewsets.ReadOnlyModelViewSet):
    queryset = InformalAction.objects.exclude(is_disabled=True)
    serializer_class = ActionSerializer


class InformalUpdateOptions(views.APIView):
    def get(self, request, format=None):
        options = dict()
        options["share_with_opts"] = [
            {
                "key": InformalUpdate.InformalShareWith.IFRC_SECRETARIAT,
                "value": "IFRC Secretariat"

            },
            {
                "key": InformalUpdate.InformalShareWith.RCRC_NETWORK,
                "value": "RCRC Network"

            },
            {
                "key": InformalUpdate.InformalShareWith.RCRC_NETWORK_AND_DONORS,
                "value": "RCRC Network and Donors"

            },
        ]
        return Response(options)

