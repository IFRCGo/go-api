from django.contrib.auth.models import Permission
from rest_framework import permissions

from dref.models import DrefFinalReport, DrefOperationalUpdate
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


class ApproveDrefPermission(permissions.BasePermission):
    message = "You need to be Superuser or Dref Regional admin to approve"

    def has_object_permission(self, request, view, obj):

        user = request.user
        region_id = obj.country.region_id

        if user.is_superuser:
            return True

        dref_region_admins_ids = [
            int(codename.replace("dref_region_admin_", ""))
            for codename in Permission.objects.filter(
                group__user=user,
                codename__startswith="dref_region_admin_",
            ).values_list("codename", flat=True)
        ]
        if region_id in dref_region_admins_ids:
            return True
        return False
