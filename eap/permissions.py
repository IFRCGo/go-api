from django.contrib.auth.models import Permission
from rest_framework.permissions import BasePermission

from api.models import Country
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

    return national_society_id in country_admin_ids


def has_regional_permission(
    user,
    region_id: int,
) -> bool:
    if user.is_superuser or user.has_perm("api.ifrc_admin"):
        return True

    regional_admin_ids = [
        int(codename.replace("region_admin_", ""))
        for codename in Permission.objects.filter(
            group__user=user,
            codename__startswith="region_admin_",
        ).values_list("codename", flat=True)
    ]

    return region_id in regional_admin_ids


class EAPRegistrationPermissions(BasePermission):
    message = "You need to be country admin or IFRC admin or superuser to create/update EAP Registration"

    def has_permission(self, request, view) -> bool:
        if request.method not in ["PUT", "PATCH", "POST"]:
            return True

        user = request.user
        national_society_id = request.data.get("national_society")
        national_society = Country.objects.filter(id=national_society_id).first()
        if not national_society:
            return False

        return (
            user.is_superuser
            or has_country_permission(user=user, national_society_id=national_society.pk)
            or has_regional_permission(
                user=user,
                region_id=national_society.region.pk,
            )
        )


class EAPBasePermission(BasePermission):
    message = "You don't have permission to create/update EAP"

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method not in ["PUT", "PATCH", "POST"]:
            return True

        user = request.user
        eap_reg_id = request.data.get("eap_registration", None) or obj.eap_registration_id
        eap_registration = EAPRegistration.objects.filter(id=eap_reg_id).first()

        assert eap_registration is not None, "EAP Registration does not exist"
        national_society_id = eap_registration.national_society_id

        return (
            user.is_superuser
            or has_country_permission(user=user, national_society_id=national_society_id)
            or has_regional_permission(
                user=user,
                region_id=eap_registration.national_society.region.pk,
            )
        )


class EAPValidatedBudgetPermission(BasePermission):
    message = "You don't have permission to upload validated budget file for this EAP"

    def has_permission(self, request, view) -> bool:
        user = request.user
        if user.is_superuser or user.has_perm("api.ifrc_admin"):
            return True
        return False
