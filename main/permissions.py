from rest_framework import permissions


class ModifyBySuperAdminOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.is_superuser

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class UseBySuperAdminOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class DenyGuestUserMutationPermission(permissions.BasePermission):
    """
    Custom permission to deny mutation actions for logged-in guest users.

    This permission class restricts all (write, update, delete) operations if the user is a guest.
    """

    def _has_permission(self, request, view):
        # Allow all safe methods (GET, HEAD, OPTIONS) which are non-mutating.
        if request.method in permissions.SAFE_METHODS:
            return True

        # For mutation methods (POST, PUT, DELETE, etc.):
        if not bool(request.user and request.user.is_authenticated):
            # Deny access if the user is not authenticated.
            return False

        return not request.user.profile.limit_access_to_guest

    def has_permission(self, request, view):
        return self._has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return self._has_permission(request, view)


class DenyGuestUserPermission(DenyGuestUserMutationPermission):
    """
    Custom permission to deny all actions(GET, POST, PUT, DELETE) for logged-in guest users.

    This permission class restricts all (read, write, update, delete) operations if the user is a guest.
    """

    def _has_permission(self, request, view):
        if not bool(request.user and request.user.is_authenticated):
            # Deny access if the user is not authenticated.
            return False

        return not request.user.profile.limit_access_to_guest
