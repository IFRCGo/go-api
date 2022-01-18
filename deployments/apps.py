from django.utils.translation import ugettext_lazy as _
from django.apps import AppConfig


class DeploymentsConfig(AppConfig):
    name = 'deployments'
    verbose_name = _('Deployments & 3W\'s (Who, What, Where)')

    def ready(self):
        import api.receivers  # noqa: F401
