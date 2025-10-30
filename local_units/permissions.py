from django.contrib.auth.models import Permission
from rest_framework import permissions

from api.models import Country
from local_units.models import LocalUnitType
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
    message = "Only Country Admins, Local Unit Validators, Region Admins, or Superusers are allowed to update Local Units."

    def has_object_permission(self, request, view, obj):
        if request.method not in ["PUT", "PATCH"]:
            return True  # Only restrict update operations

        user = request.user

        if user.is_superuser:
            return True

        country_id = obj.country_id
        country = Country.objects.get(id=country_id)
        region_id = country.region_id
        # Country admin specific permissions
        country_admin_ids = [
            int(codename.replace("country_admin_", ""))
            for codename in Permission.objects.filter(
                group__user=user,
                codename__startswith="country_admin_",
            ).values_list("codename", flat=True)
        ]
        # Regional admin specific permissions
        region_admin_ids = [
            int(codename.replace("region_admin_", ""))
            for codename in Permission.objects.filter(
                group__user=user,
                codename__startswith="region_admin_",
            ).values_list("codename", flat=True)
        ]
        if country_id in country_admin_ids or region_id in region_admin_ids:
            return True

        return (
            get_local_unit_country_validators(obj).filter(id=user.id).exists()
            or get_local_unit_region_validators(obj).filter(id=user.id).exists()
            or get_local_unit_global_validators(obj).filter(id=user.id).exists()
        )


class ExternallyManagedLocalUnitPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.is_superuser


class BulkUploadValidatorPermission(permissions.BasePermission):
    message = "You do not have permission to create bulk uploads for this country and local unit type."

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        user = request.user
        if user.is_superuser:
            return True

        country_id = request.data.get("country")
        local_unit_type_id = request.data.get("local_unit_type")

        if not country_id or not local_unit_type_id:
            return False
        try:
            country = Country.objects.get(id=country_id)
            local_unit_type = LocalUnitType.objects.get(id=local_unit_type_id)
        except (Country.DoesNotExist, LocalUnitType.DoesNotExist):
            return False

        # Country-level permission
        codename_country = f"local_unit_country_validator_{local_unit_type.id}_{country.id}"
        if user.groups.filter(permissions__codename=codename_country).exists():
            return True

        # Region-level permission
        region = country.region
        if region:
            codename_region = f"local_unit_region_validator_{local_unit_type.id}_{region.id}"
            if user.groups.filter(permissions__codename=codename_region).exists():
                return True

        # Global-level permission
        codename_global = f"local_unit_global_validator_{local_unit_type.id}"
        if user.groups.filter(permissions__codename=codename_global).exists():
            return True

        return False
