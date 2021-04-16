from rest_framework import permissions
from .models import String


class LangStringPermission(permissions.BasePermission):
    """
    Custom permission to only users to maintain strings
    """

    def has_permission(self, request, view):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests. (`view` is allowed for all)
        if request.method in permissions.SAFE_METHODS:
            return True
        return String.has_perm(request.user, view.kwargs['pk'])

    def has_object_permission(self, request, view, obj):
        return self.has_permission(self, request, view)
