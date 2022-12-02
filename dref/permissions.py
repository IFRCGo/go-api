from django.db import models

from rest_framework import permissions

from dref.models import (
    Dref,
    DrefOperationalUpdate,
)


class IsSuperAdmin(permissions.BasePermission):
    """
    Allow super user to view and perform all actions
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_superuser


class DrefViewUpdatePermission(IsSuperAdmin):
    message = "Can view and update Dref"

    def has_permission(self, request, view):
        if request.method == "POST":
            return True
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser:
            return True
        if request.method in ["PUT", "DELETE", "PATCH"]:
            return Dref.objects.filter(
                models.Q(id=obj.id, users=user) |
                models.Q(id=obj.id, created_by=user)
            ).exists()
        return True


class DrefOperationalUpdateCreatePermission(permissions.BasePermission):
    message = "Can create Operational Update for whom dref is shared with"

    def has_permission(self, request, view):
        user = request.user
        dref = request.data.get('dref')
        if request.method == "POST":
            if user.is_superuser:
                return True
            if dref:
                return Dref.objects.filter(
                    models.Q(id=dref, users=user) |
                    models.Q(id=dref, created_by=user),
                    is_published=True
                ).exists()
            return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser:
            return True
        if request.method in ["PUT", "DELETE", "PATCH"]:
            return DrefOperationalUpdate.objects.filter(
                models.Q(id=obj.id, users=user) |
                models.Q(id=obj.id, created_by=user)
            ).exists()
        return True
