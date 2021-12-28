from rest_framework import (
    viewsets,
    permissions,
    mixins
)

from informal_update.models import (
    InformalUpdate,
    InformalGraphicMap,
)
from informal_update.serializers import (
    InformalUpdateSerializer,
    InformalGraphicMapSerializer
)


class InformalUpdateViewSet(viewsets.ModelViewSet):
    serializer_class = InformalUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

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