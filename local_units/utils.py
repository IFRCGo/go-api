from django.conf import settings
from django.contrib.auth import get_user_model

from local_units.models import Validator

User = get_user_model()


def get_email_context(instance):
    from local_units.serializers import PrivateLocalUnitSerializer

    # NOTE: Passing through serializer, might need more info in the future
    local_unit_data = PrivateLocalUnitSerializer(instance).data
    email_context = {
        "id": local_unit_data["id"],
        "local_branch_name": local_unit_data["local_branch_name"],
        "country": local_unit_data["country_details"]["name"],
        "country_id": local_unit_data["country_details"]["id"],
        "update_reason_overview": local_unit_data["update_reason_overview"],
        "frontend_url": settings.GO_WEB_URL,
    }
    return email_context


def get_local_unit_country_validators(instance):
    """
    Get the user with the country level permission by each local unit type
    """
    country = instance.country
    type = instance.type
    codename = f"local_unit_country_validator_{type.id}_{country.id}"
    return User.objects.filter(groups__permissions__codename=codename).distinct()


def get_local_unit_region_validators(instance):
    """
    Get the user with the region level admin permission for the region of the instance
    """
    region = instance.country.region
    type = instance.type
    codename = f"local_unit_region_validator_{type.id}_{region.id}"
    region_validators_by_type = User.objects.filter(groups__permissions__codename=codename).distinct()
    return region_validators_by_type


def get_local_unit_global_validators(instance):
    """
    Get the user with the global validator permission by type
    """
    type = instance.type
    codename = f"local_unit_global_validator_{type.id}"
    global_validators_by_type = User.objects.filter(groups__permissions__codename=codename).distinct()
    return global_validators_by_type


def get_user_validator_level(user, local_unit):
    """
    Determines the validator level for the given local unit.
    """
    if get_local_unit_country_validators(local_unit).filter(id=user.id).exists():
        return Validator.LOCAL
    elif get_local_unit_region_validators(local_unit).filter(id=user.id).exists():
        return Validator.REGIONAL
    elif user.is_superuser or get_local_unit_global_validators(local_unit).filter(id=user.id).exists():
        return Validator.GLOBAL


def get_model_field_names(
    model,
):
    return [field.name for field in model._meta.get_fields() if not field.auto_created and field.name]


def normalize_bool(value):
    if not value:
        return False
    val = str(value).strip().lower()
    if val in ("yes"):
        return True
    if val in ("no"):
        return False


def wash(string):
    if string is None:
        return None
    return str(string).lower().replace("/", "").replace("_", "").replace(",", "").replace(" ", "")


def numerize(value):
    return value if value else 0
