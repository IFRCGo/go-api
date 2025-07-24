from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


def get_email_context(instance):
    from local_units.serializers import PrivateLocalUnitSerializer

    # NOTE: Passing through serializer, might need more info in the future
    local_unit_data = PrivateLocalUnitSerializer(instance).data
    email_context = {
        "id": local_unit_data["id"],
        "local_branch_name": local_unit_data["local_branch_name"],
        "frontend_url": settings.FRONTEND_URL,
    }
    return email_context


def get_local_admins(instance):
    """
    Get the user with the country level admin permission for the country of the instance
    """
    country_admins = User.objects.filter(groups__permissions__codename=f"country_admin_{instance.country_id}")
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


def get_model_field_names(model: type[models.Model]) -> list[str]:
    """
    Returns all field names of a model including ForeignKey and ManyToMany fields.
    """
    return [field.name for field in model._meta.get_fields() if not field.auto_created]


def wash_data(s):
    if not s:
        return ""
    return s.lower().replace("/", "").replace("_", "").replace(",", "").replace(" ", "")


def numerize(value):
    try:
        if value in [None, ""]:
            return None
        return int(value)
    except (ValueError, TypeError):
        return None


def normalize_bool(value):
    if isinstance(value, bool):
        return value
    if not value:
        return False
    val = str(value).strip().lower()
    if val in ("true", "1", "yes", "y"):
        return True
    if val in ("false", "0", "no", "n"):
        return False
    return False
