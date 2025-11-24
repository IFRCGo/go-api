import os
import typing

from django.contrib.auth.models import Permission, User
from django.core.exceptions import ValidationError

from eap.models import FullEAP, SimplifiedEAP


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


# TODO(susilnem): Add typing for FullEAP


def copy_model_instance(
    instance: SimplifiedEAP | FullEAP,
    overrides: dict[str, typing.Any] | None = None,
    exclude_clone_m2m_fields: list[str] | None = None,
) -> SimplifiedEAP | FullEAP:
    """
    Creates a copy of a Django model instance, including its many-to-many relationships.

    Args:
        instance: The Django model instance to be copied.
        overrides: A dictionary of field names and values to override in the copied instance.
        exclude_clone_m2m_fields: A list of many-to-many field names to exclude from copying

    Returns:
        A new Django model instance that is a copy of the original, with specified overrides
        applied and specified many-to-many relationships excluded.

    """

    overrides = overrides or {}
    exclude_m2m_fields = exclude_clone_m2m_fields or []

    opts = instance._meta
    data = {}

    for field in opts.fields:
        if field.auto_created:
            continue
        data[field.name] = getattr(instance, field.name)

    data[opts.pk.attname] = None

    # NOTE: Apply overrides
    data.update(overrides)

    clone_instance = instance.__class__.objects.create(**data)

    for m2m_field in opts.many_to_many:
        # NOTE: Exclude specified many-to-many fields from cloning but link to original related instances
        if m2m_field.name in exclude_m2m_fields:
            related_objects = getattr(instance, m2m_field.name).all()
            getattr(clone_instance, m2m_field.name).set(related_objects)
            continue

        related_objects = getattr(instance, m2m_field.name).all()
        cloned_related = [
            obj.__class__.objects.create(**{f.name: getattr(obj, f.name) for f in obj._meta.fields if not f.auto_created})
            for obj in related_objects
        ]
        getattr(clone_instance, m2m_field.name).set(cloned_related)

    return clone_instance
