from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RegistrationsConfig(AppConfig):
    name = "registrations"
    verbose_name = _("registrations")
