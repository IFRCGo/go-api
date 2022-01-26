from rest_framework.response import Response
from rest_framework import (
    views,
    viewsets,
    permissions,
    status,
    mixins,
    response
)
from rest_framework.decorators import action

from api.serializers import ActionSerializer
from .models import (
    InformalUpdate,
    InformalGraphicMap,
    InformalAction
)
from .serializers import (
    InformalUpdateSerializer,
    InformalGraphicMapSerializer
)
from .filter_set import InformalUpdateFilter


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

    @action(
        detail=False,
        url_path='multiple',
        methods=['POST'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def multiple_file(self, request, pk=None, version=None):
        # converts querydict to original dict
        files = dict((request.data).lists())['file']
        data = [{'file': file} for file in files]
        file_serializer = InformalGraphicMapSerializer(data=data, context={'request': request}, many=True)
        if file_serializer.is_valid():
            file_serializer.save()
            return response.Response(file_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return response.Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InformalActionViewset(viewsets.ReadOnlyModelViewSet):
    queryset = InformalAction.objects.exclude(is_disabled=True)
    serializer_class = ActionSerializer


class InformalUpdateOptions(views.APIView):
    def get(self, request, format=None):
        options = {
            'share_with_options': [
                {
                    'value': share_with[0],
                    'label': share_with[1]
                } for share_with in InformalUpdate.InformalShareWith.choices
            ]
        }
        return Response(options)

