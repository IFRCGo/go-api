from django.apps import AppConfig


class DeploymentsConfig(AppConfig):
    name = 'deployments'
    verbose_name = 'Deployments & 3W\'s (Who, What, Where)'

    def ready(self):
        import api.receivers