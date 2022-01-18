from rest_framework import permissions


class ModifyBySuperAdminOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.is_superuser

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)
