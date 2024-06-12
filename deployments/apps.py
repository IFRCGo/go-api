from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DeploymentsConfig(AppConfig):
    name = "deployments"
    verbose_name = _("Deployments & 3W's (Who, What, Where)")

    def ready(self):
        import api.receivers  # noqa: F401
