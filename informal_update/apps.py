from django.apps import AppConfig


class InformalUpdateConfig(AppConfig):
    name = 'informal_update'

    def ready(self):
        import informal_update.signals  # noqa:F401
