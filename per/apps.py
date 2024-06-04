from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PerConfig(AppConfig):
    name = "per"
    verbose_name = _("per")
