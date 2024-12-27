from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


def get_email_context(instance):
    from local_units.serializers import PrivateLocalUnitSerializer
    # NOTE: Passing through serializer, might need more info in the future
    local_unit_data = PrivateLocalUnitSerializer(instance).data
    email_context = {
        "id": local_unit_data["id"],
        "frontend_url": settings.FRONTEND_URL,
    }
    return email_context


def get_local_admins(instance):
    """
    Get the user with the country level admin permission for the country of the instance
    """
    country_admins = User.objects.filter(groups__permissions__codename=f"country_admin_{instance.country_id}").values_list(
        "id", flat=True
    )
    return country_admins


def get_region_admins(instance):
    """
    Get the user with the region level admin permission for the region of the instance
    """
    region_admins = User.objects.filter(groups__permissions__codename=f"region_admin_{instance.country.region_id}")
    return region_admins


def get_global_validators():
    """
    Get the user with the global validator permission
    """
    global_validators = User.objects.filter(groups__permissions__codename="local_unit_global_validator")
    return global_validators


def generate_email_preview_context(type):
    """
    Generate a context for the email preview
    """
    from local_units.models import LocalUnit
    from local_units.tasks import (
        send_local_unit_email,
        send_revert_email,
        send_validate_success_email,
    )

    if type == "new":
        local_unit = LocalUnit.objects.filter(is_deprecated=False, validated=False).first()
        context = send_local_unit_email(local_unit_id=local_unit.id, user_ids=get_local_admins(local_unit), new=True)
    elif type == "update":
        local_unit = LocalUnit.objects.filter(is_deprecated=False, validated=False).first()
        context = send_local_unit_email(local_unit_id=local_unit.id, user_ids=get_local_admins(local_unit), new=False)
    elif type == "validate":
        local_unit = LocalUnit.objects.filter(is_deprecated=False, validated=True).first()
        context = send_validate_success_email(local_unit_id=local_unit.id, user_id=local_unit.created_by.id, new_or_updated="New")
    elif type == "revert":
        local_unit = LocalUnit.objects.filter(is_deprecated=False, validated=True).first()
        context = send_revert_email(local_unit_id=local_unit.id, user_id=local_unit.created_by.id)

    return context
