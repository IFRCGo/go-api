from django.utils.translation import ugettext_lazy as _
from django.apps import AppConfig


class LangConfig(AppConfig):
    name = 'lang'
    vebose_name = _('lang')
