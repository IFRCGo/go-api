from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DatabankConfig(AppConfig):
    name = "databank"
    verbose_name = _("databank")
