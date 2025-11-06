from django.contrib.auth.models import Permission
from rest_framework import permissions

from dref.models import Dref, DrefFinalReport, DrefOperationalUpdate
from dref.utils import get_dref_users


class DrefOperationalUpdateUpdatePermission(permissions.BasePermission):
    message = "Can update Operational Update for whom dref is shared with"

    def has_object_permission(self, request, view, obj):
        user = request.user
        dref_objects = get_dref_users()
        user_dref_ids = []
        for dref in dref_objects:
            if user.id in dref.get("users"):
                user_dref_ids.append(dref.get("id"))
        for dref in user_dref_ids:
            return DrefOperationalUpdate.objects.filter(dref=dref).exists()
        return False


class DrefFinalReportUpdatePermission(permissions.BasePermission):
    message = "Can update Final Report for whom dref is shared with"

    def has_object_permission(self, request, view, obj):
        user = request.user
        dref_objects = get_dref_users()
        user_dref_ids = []
        for dref in dref_objects:
            if user.id in dref.get("users"):
                user_dref_ids.append(dref.get("id"))
        for dref in user_dref_ids:
            return DrefFinalReport.objects.filter(dref=dref).exists()
        return False


class PublishDrefPermission(permissions.BasePermission):
    message = "You need to be regional admin to publish dref"

    def has_object_permission(self, request, view, obj):
        region = obj.country.region.name
        codename = f"dref_region_admin_{region}"
        user = request.user
        if Permission.objects.filter(user=user, codename=codename).exists() and obj.status != Dref.Status.APPROVED:
            return True
        return False
