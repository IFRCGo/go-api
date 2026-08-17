import time
import typing
from contextlib import contextmanager

from django.conf import settings
from django.core.cache import caches
from django.db import models
from django_redis.client import DefaultClient

cache: DefaultClient = caches["default"]


class RedisLockKey(models.TextChoices):
    """
    Register for generating lock keys
    """

    _BASE = "dj-lock"

    OPERATION_LEARNING_SUMMARY = _BASE + "-operation-learning-summary-{0}"
    OPERATION_LEARNING_SUMMARY_EXPORT = _BASE + "-operation-learning-summary-export-{0}"
    MODEL_TRANSLATION = _BASE + "-{model_name}-translation-{id}"
    CLEAR_EXPIRED_DJANGO_SESSIONS = _BASE + "-clear-expired-django-sessions"


@contextmanager
def redis_lock(
    key: RedisLockKey,
    id: typing.Union[int, str, None] = None,
    model_name: typing.Optional[str] = None,
    lock_expire: int = settings.REDIS_DEFAULT_LOCK_EXPIRE,
):
    """
    Locking mechanism using Redis

    `id` is optional, for singleton locks whose key has no placeholder.
    """
    if model_name and id:
        lock_id = key.format(model_name=model_name, id=id)
    elif id is not None:
        lock_id = key.format(id)
    else:
        lock_id = str(key)
    timeout_at = time.monotonic() + lock_expire - 3
    # cache.add fails if the key already exists
    status = cache.add(lock_id, 1, lock_expire)

    try:
        yield status
    finally:
        # memcache delete is very slow, but we have to use it to take
        # advantage of using add() for atomic locking
        if time.monotonic() < timeout_at and status:
            # don't release the lock if we exceeded the timeout
            # to lessen the chance of releasing an expired lock
            # owned by someone else
            # also don't release the lock if we didn't acquire it
            cache.delete(lock_id)
