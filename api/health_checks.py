import dataclasses

import health_check
from django.conf import settings
from health_check.base import HealthCheck
from health_check.contrib import psutil as hc_psutil
from health_check.contrib import redis as hc_redis
from health_check.exceptions import ServiceReturnedUnexpectedResult, ServiceUnavailable
from redis.asyncio import Redis as RedisClient

# Seconds; an unreachable broker fails the Redis check instead of hanging the request.
REDIS_TIMEOUT = 5


class PlainName:
    """Report the check under its class name only.

    The library's names and labels include fields such as the Redis host/port and the
    pod hostname, which the public `/health-check/` response must not expose, and which
    would differ per pod.
    """

    def __repr__(self):
        return type(self).__name__

    @property
    def labels(self):
        return {"check": type(self).__name__}


class Database(PlainName, health_check.Database):
    pass


class Cache(PlainName, health_check.Cache):
    pass


class Storage(PlainName, health_check.Storage):
    pass


class Redis(PlainName, hc_redis.Redis):
    pass


class Disk(PlainName, hc_psutil.Disk):
    pass


class Memory(PlainName, hc_psutil.Memory):
    pass


@dataclasses.dataclass(repr=False)
class Elasticsearch(PlainName, HealthCheck):
    """`/health-check/` check reporting Elasticsearch cluster health.

    Added only when ELASTIC_SEARCH_HOST is configured (see get_health_checks), so
    environments without Elasticsearch still report healthy. A "red" cluster or an
    unreachable client fails the check; "yellow" (e.g. single-node, unassigned
    replicas) is treated as healthy.
    """

    def run(self):
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


def _redis_client():
    return RedisClient.from_url(
        settings.CELERY_REDIS_URL,
        socket_connect_timeout=REDIS_TIMEOUT,
        socket_timeout=REDIS_TIMEOUT,
    )


def get_health_checks():
    """Checks served by `/health-check/`, toggled per environment via settings."""
    checks = [
        Database,
        Cache,
        # The broker; the cache (a separate redis db) is covered by Cache above.
        (Redis, {"client_factory": _redis_client}),
    ]
    if not settings.HEALTH_CHECK_SKIP_STORAGE:
        checks.append(Storage)
    if settings.HEALTH_CHECK_DISK_USAGE_MAX is not None:
        checks.append((Disk, {"max_disk_usage_percent": settings.HEALTH_CHECK_DISK_USAGE_MAX}))
    if settings.HEALTH_CHECK_MEMORY_MIN is not None:
        checks.append(
            (
                Memory,
                {
                    "min_gibibytes_available": settings.HEALTH_CHECK_MEMORY_MIN / 1024,
                    # Warn on the available-memory floor only, not on a usage percentage.
                    "max_memory_usage_percent": None,
                },
            )
        )
    if settings.ELASTIC_SEARCH_HOST:
        checks.append(Elasticsearch)
    return checks
