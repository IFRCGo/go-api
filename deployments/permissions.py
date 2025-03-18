from django.contrib.auth.models import Permission
from rest_framework import permissions

from deployments.models import ERUOwner


class ERUReadinessPermission(permissions.BasePermission):
    message = "You need to be country admin to create/update ERU Readiness"

    def has_permission(self, request, view):
        user = request.user
        if user.is_superuser:
            return True

        # Check if the user is country admin or region admin
        if request.method in ["PUT", "PATCH"]:
            eru_owner = ERUOwner.objects.filter(id=request.data.get("eru_owner")).first()
            if not eru_owner:
                return False

            country_id = eru_owner.national_society_country_id
            region_id = eru_owner.national_society_country.region_id
            country_admin_ids = [
                int(codename.replace("country_admin_", ""))
                for codename in Permission.objects.filter(
                    group__user=user,
                    codename__startswith="country_admin_",
                ).values_list("codename", flat=True)
            ]

            region_admin_ids = [
                int(codename.replace("region_admin_", ""))
                for codename in Permission.objects.filter(
                    group__user=user,
                    codename__startswith="region_admin_",
                ).values_list("codename", flat=True)
            ]
            if country_id in country_admin_ids or region_id in region_admin_ids:
                return True
            return False
        return True
