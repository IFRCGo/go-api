from rest_framework import permissions

from dref.models import DrefOperationalUpdate, DrefFinalReport
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
