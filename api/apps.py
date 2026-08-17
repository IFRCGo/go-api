from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ApiConfig(AppConfig):
    name = "api"
    verbose_name = _("api")

    def ready(self):
        from django.conf import settings
        from health_check.plugins import plugin_dir

        from api.health_checks import RedisHealthCheck

        # Redis check for /health-check/. Registered here rather than by adding
        # health_check.contrib.redis to INSTALLED_APPS, so the quieter subclass is used
        # (see api/health_checks.py); it still reads settings.REDIS_URL.
        plugin_dir.register(RedisHealthCheck)

        # Expose Elasticsearch cluster health via /health-check/ (alongside
        # db/cache/psutil/redis/storage), but only when a cluster is configured,
        # so environments without Elasticsearch still report healthy.
        if settings.ELASTIC_SEARCH_HOST:
            from api.health_checks import ElasticsearchHealthCheck

            plugin_dir.register(ElasticsearchHealthCheck)
