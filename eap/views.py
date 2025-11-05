# Create your views here.
from rest_framework import permissions, viewsets

from eap.filter_set import EAPRegistrationFilterSet
from eap.models import EAPRegistration
from eap.serializers import EAPRegistrationSerializer
from main.permissions import DenyGuestUserMutationPermission


class EAPRegistrationViewset(viewsets.ModelViewSet):
    queryset = EAPRegistration.objects.all()
    serializer_class = EAPRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated, DenyGuestUserMutationPermission]
    filterset_class = EAPRegistrationFilterSet

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
