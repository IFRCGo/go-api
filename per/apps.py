from django.utils.translation import ugettext_lazy as _
from django.apps import AppConfig


class PerConfig(AppConfig):
    name = 'per'
    verbose_name = _('per')
