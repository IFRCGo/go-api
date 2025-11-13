from django.contrib.auth.models import Permission
from rest_framework.permissions import BasePermission

from eap.models import EAPRegistration


def has_country_permission(
    user,
    national_society_id: int,
) -> bool:
    if user.is_superuser or user.has_perm("api.ifrc_admin"):
        return True

    country_admin_ids = [
        int(codename.replace("country_admin_", ""))
        for codename in Permission.objects.filter(
            group__user=user,
            codename__startswith="country_admin_",
        ).values_list("codename", flat=True)
    ]
    # TODO(susilnem): Add region admin check if needed in future
    return national_society_id in country_admin_ids


class EAPRegistrationPermissions(BasePermission):
    message = "You need to be country admin or IFRC admin or superuser to create/update EAP Registration"

    def has_permission(self, request, view) -> bool:
        if request.method not in ["PUT", "PATCH", "POST"]:
            return True

        user = request.user
        national_society_id = request.data.get("national_society")
        return has_country_permission(user=user, national_society_id=national_society_id)


class EAPBasePermission(BasePermission):
    message = "You don't have permission to create/update EAP"

    def has_permission(self, request, view) -> bool:
        if request.method not in ["PUT", "PATCH", "POST"]:
            return True

        user = request.user
        eap_registration = EAPRegistration.objects.filter(id=request.data.get("eap_registration")).first()

        if not eap_registration:
            return False

        national_society_id = eap_registration.national_society_id

        return has_country_permission(
            user=user,
            national_society_id=national_society_id,
        )


class EAPValidatedBudgetPermission(BasePermission):
    message = "You don't have permission to upload validated budget file for this EAP"

    def has_permission(self, request, view) -> bool:
        user = request.user
        if user.is_superuser or user.has_perm("api.ifrc_admin"):
            return True
        return False
