import os

from django.contrib.auth.models import Permission, User
from django.core.exceptions import ValidationError


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
