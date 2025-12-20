import os
from typing import Any, Dict, Set, TypeVar

from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.core.exceptions import ValidationError
from django.db import models

from api.models import Region, RegionName
from eap.models import EAPType, FullEAP, SimplifiedEAP

REGION_EMAIL_MAP: dict[RegionName, list[str]] = {
    RegionName.AFRICA: settings.EMAIL_EAP_AFRICA_COORDINATORS,
    RegionName.AMERICAS: settings.EMAIL_EAP_AMERICAS_COORDINATORS,
    RegionName.ASIA_PACIFIC: settings.EMAIL_EAP_ASIA_PACIFIC_COORDINATORS,
    RegionName.EUROPE: settings.EMAIL_EAP_EUROPE_COORDINATORS,
    RegionName.MENA: settings.EMAIL_EAP_MENA_COORDINATORS,
}


def get_coordinator_emails_by_region(region: Region | None) -> list[str]:
    """
    This function uses the REGION_EMAIL_MAP dictionary to map Region name to the corresponding list of email addresses.
    Args:
        region: Region instance for which the coordinator emails are needed.
    Returns:
        List of email addresses corresponding to the region coordinators.
        Returns an empty list if the region is None or not found in the mapping.
    """
    if not region:
        return []

    return REGION_EMAIL_MAP.get(region.name, [])


# TODO @sudip-khanal: Add files to email context after implementing file sending in email notification
# also include the deadline field once it added to the model.


def get_eap_email_context(instance):
    from eap.serializers import EAPRegistrationSerializer

    eap_registration_data = EAPRegistrationSerializer(instance).data

    email_context = {
        "registration_id": eap_registration_data["id"],
        "eap_type_display": eap_registration_data["eap_type_display"],
        "country_name": eap_registration_data["country_details"]["name"],
        "national_society": eap_registration_data["national_society_details"]["society_name"],
        "supporting_partners": eap_registration_data["partners_details"],
        "disaster_type": eap_registration_data["disaster_type_details"]["name"],
        "ns_contact_name": eap_registration_data["national_society_contact_name"],
        "ns_contact_email": eap_registration_data["national_society_contact_email"],
        "ns_contact_phone": eap_registration_data["national_society_contact_phone_number"],
        "dead_line": eap_registration_data["dead_line"],
        "frontend_url": settings.GO_WEB_URL,
        # "review_checklist_file":eap_registration_data["review_checklist_file"],
        # "validated_budget_file":eap_registration_data["validated_budget_file"],
    }

    if instance.get_eap_type_enum == EAPType.SIMPLIFIED_EAP:
        latest_eap_data = instance.latest_simplified_eap
        latest_version = instance.latest_simplified_eap.version
        qs = SimplifiedEAP.objects.filter(eap_registration=instance, version__lt=latest_version).order_by("-version").first()
        previous_version = qs.version if qs else None
    else:
        latest_eap_data = instance.latest_full_eap
        latest_version = instance.latest_full_eap
        qs = FullEAP.objects.filter(eap_registration=instance, version__lt=latest_version).order_by("-version").first()
        previous_version = qs.version if qs else None

    email_context.update(
        {
            "people_targeted": latest_eap_data.people_targeted,
            "total_budget": latest_eap_data.total_budget,
            "latest_version": latest_eap_data.version,
            "previous_version": previous_version,
            # "updated_checklist_file": latest_eap_data.updated_checklist_file,
            # "budget_file":latest_eap_data.budget_file,
        }
    )
    return email_context


def has_country_permission(user: User, country_id: int) -> bool:
    """Checks if the user has country admin permission."""
    country_admin_ids = [
        int(codename.replace("country_admin_", ""))
        for codename in Permission.objects.filter(
            group__user=user,
            codename__startswith="country_admin_",
        ).values_list("codename", flat=True)
    ]

    return country_id in country_admin_ids


def is_user_ifrc_admin(user: User) -> bool:
    """
    Checks if the user has IFRC Admin or superuser permissions.

    Returns True if the user is a superuser or has the IFRC Admin permission, False otherwise.
    """

    if user.is_superuser or user.has_perm("api.ifrc_admin"):
        return True
    return False


def validate_file_extention(filename: str, allowed_extensions: list[str]):
    """
    This function validates a file's extension against a list of allowed extensions.
    Args:
        filename: The name of the file to validate.
    Returns:
        ValidationError: If the file extension is not allowed.
    """

    extension = os.path.splitext(filename)[1].replace(".", "")
    if extension.lower() not in allowed_extensions:
        raise ValidationError(f"Invalid uploaded file extension: {extension}, Supported only {allowed_extensions} Files")


T = TypeVar("T", bound=models.Model)


def copy_model_instance(
    instance: T,
    overrides: Dict[str, Any] | None = None,
    exclude_clone_m2m_fields: Set[str] | None = None,
    clone_cache: Dict[tuple[type[T], int], T] | None = None,
) -> T:
    """
    Recursively clone a Django model instance, including nested M2M fields.
    Uses clone_cache to prevent infinite loops and duplicated clones.
    Args:
        instance: The Django model instance to clone.
        overrides: A dictionary of field names and values to override in the cloned instance.
        exclude_clone_m2m_fields: A set of M2M field names to exclude from cloning (
            these will link to existing related objects instead).
        clone_cache: A dictionary to keep track of already cloned instances to prevent infinite loops.
    Returns:
        The cloned Django model instance.

    """

    overrides = overrides or {}
    exclude_m2m = exclude_clone_m2m_fields or set()
    clone_cache = clone_cache or {}

    key = (instance.__class__, instance.pk)

    # already cloned -> return that clone
    if key in clone_cache:
        return clone_cache[key]

    opts = instance._meta
    data: Dict[str, Any] = {}

    # Cloning standard fields
    for field in opts.fields:
        if field.auto_created:
            continue
        data[field.name] = getattr(instance, field.name)

    data[opts.pk.attname] = None

    data.update(overrides)

    clone: T = instance.__class__.objects.create(**data)
    # NOTE: Register the clone in cache before cloning M2M to handle circular references
    clone_cache[key] = clone

    for m2m_field in opts.many_to_many:
        name = m2m_field.name

        # excluded M2M: only link to existing related objects
        if name in exclude_m2m:
            related = getattr(instance, name).all()
            getattr(clone, name).set(related)
            continue

        related = getattr(instance, name).all()
        cloned_related: list[T] = []

        for obj in related:
            overrides_obj = {}
            if hasattr(obj, "previous_id"):
                overrides_obj["previous_id"] = obj.pk

            cloned_obj = copy_model_instance(
                obj,
                overrides=overrides_obj,
                exclude_clone_m2m_fields=exclude_m2m,
                clone_cache=clone_cache,
            )
            cloned_related.append(cloned_obj)

        getattr(clone, name).set(cloned_related)

    return clone
