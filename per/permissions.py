from rest_framework import permissions

from api.models import Region


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
