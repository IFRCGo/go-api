from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied

from local_units.models import Validator

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
    raise PermissionDenied("You do not have permission to validate this local unit..")
