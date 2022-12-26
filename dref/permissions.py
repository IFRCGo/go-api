from django.db import models

from rest_framework import permissions

from dref.models import (
    Dref,
    DrefOperationalUpdate,
)
from dref.utils import get_users_in_dref, get_users_in_dref_operational_update


class IsSuperAdmin(permissions.BasePermission):
    """
    Allow super user to view and perform all actions
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_superuser


class DrefViewUpdatePermission(permissions.BasePermission):
    message = "Can't view and update Dref"
    pass


class DrefOperationalUpdateCreatePermission(permissions.BasePermission):
    message = "Can create Operational Update for whom dref is shared with"

    def has_permission(self, request, view):
        pass

    def has_object_permission(self, request, view, obj):
        pass
