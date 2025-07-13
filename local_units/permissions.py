from rest_framework import permissions

from local_units.utils import (
    get_global_validators_by_type,
    get_local_unit_validators_by_type,
    get_region_validators_by_type,
)


class ValidateLocalUnitPermission(permissions.BasePermission):
    message = "You need to be super user/ global validator/ region validator/ country validator to validate local unit"

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser:
            return True
        elif get_global_validators_by_type(obj).filter(id=user.id):
            return True
        elif get_region_validators_by_type(obj).filter(id=user.id):
            return True
        elif get_local_unit_validators_by_type(obj).filter(id=user.id):
            return True
        return False


class IsAuthenticatedForLocalUnit(permissions.BasePermission):
    message = "Only validators or superusers are allowed to update Local Units"

    def has_object_permission(self, request, view, obj):
        if request.method not in ["PUT", "PATCH"]:
            return True  # Only restrict update operations

        user = request.user

        if user.is_superuser:
            return True

        return (
            get_local_unit_validators_by_type(obj).filter(id=user.id).exists()
            or get_region_validators_by_type(obj).filter(id=user.id).exists()
            or get_global_validators_by_type(obj).filter(id=user.id).exists()
        )
