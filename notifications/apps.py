from django.utils.translation import gettext_lazy as _
from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    name = 'notifications'
    verbose_name = _('notifications')
