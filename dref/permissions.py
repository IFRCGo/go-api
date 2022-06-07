from django.db import models

from rest_framework import permissions

from dref.models import Dref


class DrefOperationalUpdateCreatePermission(permissions.BasePermission):
    message = "Can create Operational Update for whom dref is shared with"

    def has_permission(self, request, view):
        if request.method != "POST":
            return True
        user = request.user
        dref = request.data.get('dref')
        if dref:
            return Dref.objects.filter(
                models.Q(id=dref, users=user) |
                models.Q(id=dref, created_by=user)
            ).exists()
        return True
