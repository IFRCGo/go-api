from django.db import models

from rest_framework import (
    views,
    viewsets,
    response,
    permissions,
    status,
    mixins
)
from rest_framework.decorators import action
from dref.models import (
    Dref,
    NationalSocietyAction,
    PlannedIntervention,
    IdentifiedNeed,
    DrefFile
)
from dref.serializers import (
    DrefSerializer,
    NationalSocietyActionSerializer,
    PlannedInterventionSerializer,
    IdentifiedNeedSerializer,
    DrefFileSerializer
)
from dref.filter_set import DrefFilter


class DrefViewSet(viewsets.ModelViewSet):
    # TODO: Need to add permission to delete?
    serializer_class = DrefSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = DrefFilter

    def get_queryset(self):
        return Dref.objects\
            .filter(
                models.Q(created_by=self.request.user) |
                models.Q(users=self.request.user)
            )\
            .prefetch_related(
                'planned_interventions',
                'needs_identified',
                'national_society_actions',
                'users'
            )


class DrefOptionsView(views.APIView):
    """
    Options for various attrivute related to Dref
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, version=None):
        options = {
            'status': [
                {
                    'key': status.value,
                    'value': status.label
                } for status in Dref.Status
            ],
            'type_of_onset': [
                {
                    'key': onset.value,
                    'value': onset.label
                } for onset in Dref.OnsetType
            ],
            'disaster_category': [
                {
                    'key': disaster.value,
                    'value': disaster.label
                } for disaster in Dref.DisasterCategory
            ],
            'planned_interventions': [
                {
                    'key': intervention[0],
                    'value': intervention[1]
                } for intervention in PlannedIntervention.Title.choices
            ],
            'needs_identified': [
                {
                    'key': need[0],
                    'value': need[1]
                } for need in IdentifiedNeed.Title.choices
            ],
            'national_society_actions': [
                {
                    'key': action[0],
                    'value': action[1]
                } for action in NationalSocietyAction.Title.choices
            ]
        }
        return response.Response(options)


class NationalSocietyActionViewSet(viewsets.ModelViewSet):
    serializer_class = NationalSocietyActionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = NationalSocietyAction.objects.all()


class PlannedInterventionViewSet(viewsets.ModelViewSet):
    serializer_class = PlannedInterventionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = PlannedIntervention.objects.all()


class IdentifiedNeedViewSet(viewsets.ModelViewSet):
    serializer_class = IdentifiedNeedSerializer
    permission_class = [permissions.IsAuthenticated]
    queryset = IdentifiedNeed.objects.all()


class DrefFileViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    permission_class = [permissions.IsAuthenticated]
    serializer_class = DrefFileSerializer

    def get_queryset(self):
        return DrefFile.objects.filter(created_by=self.request.user)

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
        file_serializer = DrefFileSerializer(data=data, context={'request': request}, many=True)
        if file_serializer.is_valid():
            file_serializer.save()
            return response.Response(file_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return response.Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
