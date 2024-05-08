from rest_framework import permissions


class ValidateLocalUnitPermission(permissions.BasePermission):
    message = "You need to be super user to validate local unit"

    def has_object_permission(self, request, view, object):
        user = request.user
        if user.is_superuser:
            return True
        return False


class IsAuthenticatedForLocalUnit(permissions.BasePermission):
    message = "Only Authenticated users allowed to create/update Local Units"

    def has_permission(self, request, view):
        if request.method in ["POST", "PUT", "PATCH"]:
            return request.user and request.user.is_authenticated
        return True
