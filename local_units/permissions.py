from rest_framework import permissions

from django.contrib.auth.models import Permission


class ValidateLocalUnitPermission(permissions.BasePermission):
    message = "You need to be super user to validate local unit"

    def has_object_permission(self, request, view, object):
        user = request.user
        if user.is_superuser:
            return True
        return False
