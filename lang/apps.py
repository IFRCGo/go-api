from django.utils.translation import gettext_lazy as _
from django.apps import AppConfig


class LangConfig(AppConfig):
    name = 'lang'
    verbose_name = _('lang')
