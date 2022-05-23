from django.utils.translation import gettext_lazy as _
from django.apps import AppConfig


class RegistrationsConfig(AppConfig):
    name = 'registrations'
    verbose_name = _('registrations')
