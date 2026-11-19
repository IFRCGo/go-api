from pydoc import locate

from django.conf import settings
from django.core.checks import Error, Tags, register


@register(Tags.compatibility)
def celery_beat_tasks(app_configs, **kwargs):
    """Catch a typo'd SCHEDULES task path now, not on beat's first tick."""
    from main.cronjobs import SCHEDULES

    errors = []
    for name, config in SCHEDULES.items():
        if locate(config.task) is None:
            errors.append(Error(f"Celery beat <{name}> task is incorrect: {config.task}"))
    return errors


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
