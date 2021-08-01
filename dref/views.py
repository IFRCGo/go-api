from rest_framework import (
    viewsets,
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
    # TODO: Need to add permission to delete
    serializer_class = DrefSerializer
    permission_class = [permissions.IsAuthenticated]
    filterset_class = DrefFilter

    def get_queryset(self):
        return Dref.objects.prefetch_related(
            'planned_interventions', 'needs_identified', 'national_society_actions'
        )


class NationalSocietyActionViewSet(viewsets.ModelViewSet):
    serializer_class = NationalSocietyActionSerializer
    permission_class = [permissions.IsAuthenticated]
    queryset = NationalSocietyAction.objects.all()


class PlannedInterventionViewSet(viewsets.ModelViewSet):
    serializer_class = PlannedInterventionSerializer
    permission_class = [permissions.IsAuthenticated]
    queryset = PlannedIntervention.objects.all()


class IdentifiedNeedViewSet(viewsets.ModelViewSet):
    serializer_class = IdentifiedNeedSerializer
    permission_class = [permissions.IsAuthenticated]
    queryset = IdentifiedNeed.objects.all()
