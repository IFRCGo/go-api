from rest_framework import permissions

from local_units.utils import (
    get_local_unit_country_validators,
    get_local_unit_global_validators,
    get_local_unit_region_validators,
)


class ValidateLocalUnitPermission(permissions.BasePermission):
    message = "You don't have permissions to validate"

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser:
            return True
        return (
            get_local_unit_country_validators(obj).filter(id=user.id).exists()
            or get_local_unit_region_validators(obj).filter(id=user.id).exists()
            or get_local_unit_global_validators(obj).filter(id=user.id).exists()
        )


class IsAuthenticatedForLocalUnit(permissions.BasePermission):
    message = "Only validators or superusers are allowed to update Local Units"

    def has_object_permission(self, request, view, obj):
        if request.method not in ["PUT", "PATCH"]:
            return True  # Only restrict update operations

        user = request.user

        if user.is_superuser:
            return True

        return (
            get_local_unit_country_validators(obj).filter(id=user.id).exists()
            or get_local_unit_region_validators(obj).filter(id=user.id).exists()
            or get_local_unit_global_validators(obj).filter(id=user.id).exists()
        )
