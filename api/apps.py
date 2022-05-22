from django.utils.translation import ugettext_lazy as _
from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = 'api'
    verbose_name = _('api')
