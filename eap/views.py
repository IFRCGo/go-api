# Create your views here.
from rest_framework import permissions, viewsets

from eap.filter_set import DevelopmentRegistrationEAPFilterSet
from eap.models import DevelopmentRegistrationEAP
from eap.serializers import DevelopmentRegistrationEAPSerializer
from main.permissions import DenyGuestUserMutationPermission


class DevelopmentRegistrationEAPViewset(viewsets.ModelViewSet):
    queryset = DevelopmentRegistrationEAP.objects.all()
    serializer_class = DevelopmentRegistrationEAPSerializer
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserMutationPermission]
    filterset_class = DevelopmentRegistrationEAPFilterSet

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "created_by",
                "modified_by",
                "national_society",
                "disaster_type",
            )
            .prefetch_related(
                "partners",
            )
        )
