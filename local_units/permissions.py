from django.contrib.auth.models import Group, Permission
from rest_framework import permissions


class ValidateLocalUnitPermission(permissions.BasePermission):
    message = "You need to be super user/ global validator/ region admin/ country admin to validate local unit"

    def has_object_permission(self, request, view, object):
        user = request.user

        # Check if user is superuser or in Local Unit Global Validators group
        group_queryset = Group.objects.filter(
            name="Local Unit Global Validators",
            user=user,
        ).first()

        if user.is_superuser or group_queryset:
            return True
        country_admin_ids = [
            int(codename.replace("country_admin_", ""))
            for codename in Permission.objects.filter(
                group__user=user,
                codename__startswith="country_admin_",
            ).values_list("codename", flat=True)
        ]
        region_admin_ids = [
            int(codename.replace("region_admin_", ""))
            for codename in Permission.objects.filter(
                group__user=user,
                codename__startswith="region_admin_",
            ).values_list("codename", flat=True)
        ]
        if object.country_id in country_admin_ids or object.country.region_id in region_admin_ids:
            return True
        return False


class IsAuthenticatedForLocalUnit(permissions.BasePermission):
    message = "Only Authenticated users allowed to create/update Local Units"

    def has_permission(self, request, view):
        if request.method in ["POST", "PUT", "PATCH"]:
            return request.user and request.user.is_authenticated
        return True
