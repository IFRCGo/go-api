import os
from typing import Any, Dict, Set, TypeVar

from django.contrib.auth.models import Permission, User
from django.core.exceptions import ValidationError
from django.db import models


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

    # already cloned → return that clone
    if key in clone_cache:
        return clone_cache[key]

    opts = instance._meta
    data = {}

    # Cloning standard fields
    for field in opts.fields:
        if field.auto_created:
            continue
        data[field.name] = getattr(instance, field.name)

    data[opts.pk.attname] = None

    data.update(overrides)

    clone = instance.__class__.objects.create(**data)
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
        cloned_related = [
            copy_model_instance(
                obj,
                overrides=None,
                exclude_clone_m2m_fields=exclude_m2m,
                clone_cache=clone_cache,
            )
            for obj in related
        ]

        getattr(clone, name).set(cloned_related)

    return clone
