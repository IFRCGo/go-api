from rest_framework.response import Response
from rest_framework import (
    views,
    viewsets,
    permissions,
    mixins
)

from informal_update.models import (
    InformalUpdate,
    InformalGraphicMap,
    InformalAction
)

from informal_update.serializers import (
    InformalUpdateSerializer,
    InformalGraphicMapSerializer
)

from .filter_set import InformalUpdateFilter
from api.serializers import ActionSerializer


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
        options = {
            'share_with_options': [
                {
                    'key': share_with[0],
                    'value': share_with[1]
                } for share_with in InformalUpdate.InformalShareWith.choices
            ]
        }
        return Response(options)

