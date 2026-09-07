from health_check.backends import HealthCheck
from health_check.contrib.redis.backends import RedisHealthCheck as BaseRedisHealthCheck
from health_check.exceptions import ServiceReturnedUnexpectedResult, ServiceUnavailable
from redis import Redis as RedisClient


class RedisHealthCheck(BaseRedisHealthCheck):
    """`/health-check/` redis backend, minus the upstream stray stdout line.

    django-health-check 3.24.0 builds the client from `settings.REDIS_URL` in
    `__post_init__` and writes a debug line to stdout while doing so — the plugin is
    constructed per request, so every poll of the endpoint leaves a junk line in the
    application log. Passing a ready-made client at registration is not an option:
    the plugin registry deep-copies each plugin's options per request and a live
    redis client is not copyable. So build it here instead, without the noise.
    """

    def __post_init__(self):
        if not self.client:
            self.client = RedisClient.from_url(self.redis_url, **self.redis_url_options)


class ElasticsearchHealthCheck(HealthCheck):
    """`/health-check/` backend reporting Elasticsearch cluster health.

    Registered only when ELASTIC_SEARCH_HOST is configured (see ApiConfig.ready),
    so environments without Elasticsearch still report healthy. A "red" cluster or
    an unreachable client fails the check; "yellow" (e.g. single-node, unassigned
    replicas) is treated as healthy.
    """

    def check_status(self):
        from api.esconnection import ES_CLIENT

        if ES_CLIENT is None:
            raise ServiceUnavailable("Elasticsearch host is not configured")
        try:
            health = ES_CLIENT.cluster.health()
        except Exception as exc:
            raise ServiceUnavailable(f"Elasticsearch cluster unreachable: {exc}")
        status = (health or {}).get("status")
        if status == "red":
            raise ServiceReturnedUnexpectedResult(f"Elasticsearch cluster status is {status}")

    def __repr__(self):
        return "Elasticsearch"
