from django.conf import settings
from django.contrib.auth import get_user_model

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


def get_local_unit_validators_by_type(instance):
    """
    Get the user with the country level permission by each local unit type
    """
    country = instance.country
    type = instance.type
    country_name = country.name.lower().replace(" ", "_")
    type_name = type.name.lower().replace(" ", "_")
    codename = f"local_unit_validator_{country_name}_{type_name}"
    return User.objects.filter(groups__permissions__codename=codename).distinct()


def get_region_validators_by_type(instance):
    """
    Get the user with the region level admin permission for the region of the instance
    """
    region = instance.country.region
    type = instance.type
    region_label = region.label.lower().replace(" ", "_")
    type_name = type.name.lower().replace(" ", "_")
    codename = f"local_unit_validator_{region_label}_{type_name}"
    region_validators_by_type = User.objects.filter(groups__permissions__codename=codename).distinct()
    return region_validators_by_type


def get_global_validators_by_type(instance):
    """
    Get the user with the global validator permission by type
    """
    type = instance.type
    type_name = type.name.lower().replace(" ", "_")
    codename = f"local_unit_global_validator_{type_name}"
    global_validators_by_type = User.objects.filter(groups__permissions__codename=codename).distinct()
    return global_validators_by_type
