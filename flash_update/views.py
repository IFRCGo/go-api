from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import (
    views,
    viewsets,
    permissions,
    status,
    mixins,
    response,
)
from rest_framework.decorators import action

from api.serializers import ActionSerializer
from .models import (
    FlashUpdate,
    FlashGraphicMap,
    FlashAction,
    DonorGroup,
    Donors,
    FlashUpdateShare,
)
from .serializers import (
    FlashUpdateSerializer,
    FlashGraphicMapSerializer,
    DonorGroupSerializer,
    DonorsSerializer,
    ShareFlashUpdateSerializer,
)
from .filter_set import FlashUpdateFilter


class FlashUpdateViewSet(viewsets.ModelViewSet):
    serializer_class = FlashUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = FlashUpdateFilter

    def get_queryset(self):
        return FlashUpdate.objects.all().order_by('-created_at').distinct()


class FlashUpdateFileViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    permission_class = [permissions.IsAuthenticated]
    serializer_class = FlashGraphicMapSerializer

    def get_queryset(self):
        return FlashGraphicMap.objects.all()

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
        if len(data) > 3:
            raise serializers.ValidationError("Number of files selected should not be greater than 3")
        file_serializer = FlashGraphicMapSerializer(data=data, context={'request': request}, many=True)
        if file_serializer.is_valid():
            file_serializer.save()
            return response.Response(file_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return response.Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FlashActionViewset(viewsets.ReadOnlyModelViewSet):
    queryset = FlashAction.objects.exclude(is_disabled=True)
    serializer_class = ActionSerializer


class FlashUpdateOptions(views.APIView):
    def get(self, request, format=None):
        options = {
            'share_with_options': [
                {
                    'value': value,
                    'label': label,
                } for value, label in FlashUpdate.FlashShareWith.choices
            ]
        }
        return Response(options)


class DonorGroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DonorGroup.objects.all()
    serializer_class = DonorGroupSerializer


class DonorsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Donors.objects.all()
    serializer_class = DonorsSerializer


class ShareFlashUpdateViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = FlashUpdateShare.objects.all()
    serializer_class = ShareFlashUpdateSerializer
    permission_class = [permissions.IsAuthenticated]
