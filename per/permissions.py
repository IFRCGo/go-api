from django.contrib.auth.models import Permission

from rest_framework import permissions

from api.models import Region
from per.models import OpsLearning


class CustomObjectPermissions(permissions.DjangoObjectPermissions):
    """
    Similar to `DjangoObjectPermissions`, but adding 'view' permissions.
    Still not used
    """

    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": ["%(app_label)s.view_%(model_name)s"],
        "HEAD": ["%(app_label)s.view_%(model_name)s"],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }


class PerPermission(permissions.BasePermission):
    message = "You don't have permission to Create/Update Per Overview"

    def has_permission(self, request, view):
        user = request.user
        if user.is_superuser or user.has_perm("api.per_core_admin"):
            return True

        if view.action in ["create", "update"]:
            country_id = self.get_country_id_from_request_data(request.data)
            region_id = self.get_region_id_from_request_data(request.data)
            if country_id or region_id:
                return self.has_country_permission(user, country_id) or self.has_region_permission(user, region_id)

        return True

    def has_country_permission(self, user, country_id):
        country_permission_codename = f"api.per_country_admin_{country_id}"
        return user.has_perm(country_permission_codename)

    def has_region_permission(self, user, region_id):
        region_permission_codename = f"api.per_region_admin_{region_id}"
        return user.has_perm(region_permission_codename)

    def get_country_id_from_request_data(self, request_data):
        country_id = request_data.get("country")
        return country_id

    def get_region_id_from_request_data(self, request_data):
        country_id = request_data.get("country")
        region = Region.objects.filter(country=country_id).first()
        return region and region.id


class PerDocumentUploadPermission(PerPermission):
    message = "You don't have permission to Upload Document"


class OpsLearningPermission(permissions.BasePermission):
    message = "You don't have permission for Ops Learning records"

    def has_permission(self, request, view):
        if (
            request.method in permissions.SAFE_METHODS or
            OpsLearning.is_user_admin(request.user)
        ):
            return True
        return False


class PerGeneralPermission(permissions.BasePermission):
    message = "You don't have permission"

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser or user.has_perm("api.per_core_admin"):
            return True
        country_id = obj.overview.country_id
        # also get region from the country
        region_id = obj.overview.country.region_id

        # Check if country admin
        per_admin_country_id = [
            codename.replace('per_country_admin_', '')
            for codename in Permission.objects.filter(
                group__user=user,
                codename__startswith='per_country_admin_',
            ).values_list('codename', flat=True)
        ]
        per_admin_country_id = list(map(int, per_admin_country_id))
        per_admin_region_id = [
            codename.replace('per_region_admin_', '')
            for codename in Permission.objects.filter(
                group__user=user,
                codename__startswith='per_region_admin_',
            ).values_list('codename', flat=True)
        ]
        per_admin_region_id = list(map(int, per_admin_region_id))
        if country_id in per_admin_country_id or region_id in per_admin_region_id:
            return True
        return False
