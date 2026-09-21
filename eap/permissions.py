from rest_framework.permissions import BasePermission

from api.models import Country
from eap.models import EAPRegistration
from eap.utils import get_admin_ids


def has_country_permission(
    user,
    national_society_id: int,
) -> bool:
    if user.is_superuser or user.has_perm("api.ifrc_admin"):
        return True

    return national_society_id in get_admin_ids(user, "country_admin_")


def has_regional_permission(
    user,
    region_id: int,
) -> bool:
    if user.is_superuser or user.has_perm("api.ifrc_admin"):
        return True

    return region_id in get_admin_ids(user, "region_admin_")


def has_creator_or_shared_permission(
    user,
    eap_registration: EAPRegistration,
) -> bool:
    return eap_registration.created_by_id == user.id or eap_registration.users.filter(id=user.id).exists()


class EAPRegistrationPermissions(BasePermission):
    message = "You need to be country admin or IFRC admin or superuser to create/update EAP Registration"

    def has_permission(self, request, view) -> bool:
        # NOTE: Updates are checked per object instead, so shared users are allowed through.
        if request.method != "POST":
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

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method not in ["PUT", "PATCH", "POST"]:
            return True

        user = request.user

        return (
            user.is_superuser
            or has_creator_or_shared_permission(user=user, eap_registration=obj)
            or has_country_permission(user=user, national_society_id=obj.national_society_id)
            or has_regional_permission(
                user=user,
                region_id=obj.national_society.region.pk,
            )
        )


class EAPBasePermission(BasePermission):
    message = "You don't have permission to create/update EAP"

    def can_write(self, user, eap_reg_id) -> bool:
        eap_registration = EAPRegistration.objects.filter(id=eap_reg_id).first()
        if not eap_registration:
            return False

        return (
            user.is_superuser
            or has_creator_or_shared_permission(user=user, eap_registration=eap_registration)
            or has_country_permission(user=user, national_society_id=eap_registration.national_society_id)
            or has_regional_permission(
                user=user,
                region_id=eap_registration.national_society.region.pk,
            )
        )

    def has_permission(self, request, view) -> bool:
        # NOTE: has_object_permission is never called on create, so the EAP Registration in the
        # payload has to be checked here.
        if request.method != "POST":
            return True

        return self.can_write(request.user, request.data.get("eap_registration"))

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method not in ["PUT", "PATCH", "POST"]:
            return True

        return self.can_write(
            request.user,
            request.data.get("eap_registration", None) or obj.eap_registration_id,
        )


class EAPRevisePermission(EAPBasePermission):
    message = "You don't have permission to revise this EAP"

    def has_permission(self, request, view) -> bool:
        return True


class EAPValidatedBudgetPermission(BasePermission):
    message = "You don't have permission to upload validated budget file for this EAP"

    def has_permission(self, request, view) -> bool:
        user = request.user
        if user.is_superuser or user.has_perm("api.ifrc_admin"):
            return True
        return False
