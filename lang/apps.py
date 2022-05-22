from django.utils.translation import ugettext_lazy as _
from django.apps import AppConfig


class LangConfig(AppConfig):
    name = 'lang'
    verbose_name = _('lang')
