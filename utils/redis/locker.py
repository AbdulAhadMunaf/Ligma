import redis
from django.conf import settings

LOCK_TIMEOUT = 60  # Lock timeout in seconds

if settings.CELERY_BROKER_URL.startswith("redis://"):
    redis_client = redis.StrictRedis.from_url(settings.CELERY_BROKER_URL)
else:
    redis_client = None  # For non-Redis configurations


def acquire_lock(lock_name, lock_timeout=LOCK_TIMEOUT):
    """Acquire a distributed lock using Redis."""
    return redis_client.set(lock_name, "locked", ex=lock_timeout, nx=True)


def release_lock(lock_name):
    """Release a distributed lock using Redis."""
    redis_client.delete(lock_name)
