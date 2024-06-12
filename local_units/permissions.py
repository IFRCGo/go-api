from django.contrib.auth.models import Permission
from rest_framework import permissions


class ValidateLocalUnitPermission(permissions.BasePermission):
    message = "You need to be super user/ country admin to validate local unit"

    def has_object_permission(self, request, view, object):
        user = request.user
        if user.is_superuser:
            return True
        country_admin_ids = [
            int(codename.replace("country_admin_", ""))
            for codename in Permission.objects.filter(
                group__user=user,
                codename__startswith="country_admin_",
            ).values_list("codename", flat=True)
        ]
        if object.country_id in country_admin_ids:
            return True
        return False


class IsAuthenticatedForLocalUnit(permissions.BasePermission):
    message = "Only Authenticated users allowed to create/update Local Units"

    def has_permission(self, request, view):
        if request.method in ["POST", "PUT", "PATCH"]:
            return request.user and request.user.is_authenticated
        return True
