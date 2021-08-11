from os import stat
from rest_framework import (
    views,
    viewsets,
    response,
    permissions
)

from dref.models import (
    Dref,
    NationalSocietyAction,
    PlannedIntervention,
    IdentifiedNeed
)
from dref.serializers import (
    DrefSerializer,
    NationalSocietyActionSerializer,
    PlannedInterventionSerializer,
    IdentifiedNeedSerializer
)
from dref.filter_set import DrefFilter


class DrefViewSet(viewsets.ModelViewSet):
    # TODO: Need to add permission to delete?
    serializer_class = DrefSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = DrefFilter

    def get_queryset(self):
        return Dref.objects.prefetch_related(
            'planned_interventions', 'needs_identified', 'national_society_actions'
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
