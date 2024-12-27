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


def generate_email_preview_context(type: str) -> dict:
    """
    Generate a context for the email preview
    """
    if type == "new":
        context = {"new_local_unit": True, "validator_email": "Test Validator", "full_name": "Test User"}
    elif type == "update":
        context = {"update_local_unit": True, "validator_email": "Test Validator", "full_name": "Test User"}
    elif type == "validate":
        context = {"validate_success": True, "full_name": "Test User"}
    elif type == "revert":
        context = {"revert_reason": "Test Reason", "full_name": "Test User"}
    elif type == "deprecate":
        context = {"deprecate_local_unit": True, "deprecate_reason": "Test Deprecate Reason", "full_name": "Test User"}
    elif type == "regional":
        context = {"regional_admin": True, "full_name": "Regional User"}
    elif type == "global":
        context = {"global_admin": True, "full_name": "Global User"}
    else:
        context = {}
    return context
