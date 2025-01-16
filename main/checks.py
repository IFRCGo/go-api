from django.conf import settings
from django.core.checks import Error, Tags, register


@register(Tags.compatibility)
def oauth2_check(app_configs, **kwargs):
    if not settings.OIDC_ENABLE:
        return []

    errors = []
    for label, value in [
        ("OIDC_RSA_PRIVATE_KEY", settings.OIDC_RSA_PRIVATE_KEY),
        ("OIDC_RSA_PUBLIC_KEY", settings.OIDC_RSA_PUBLIC_KEY),
    ]:
        if value not in [None, ""]:
            continue
        errors.append(Error(f"When OIDC_ENABLE is enabled, {label} shouldn't be empty"))
    return errors
