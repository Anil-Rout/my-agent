# cache.py — Upstash Redis cache
# Lazy initialization — only connects when first used, never crashes startup

from upstash_redis import Redis
from config.settings import REDIS_URL, REDIS_TOKEN

_redis = None


def _get_redis() -> Redis | None:
    global _redis
    if _redis is not None:
        return _redis
    if not REDIS_URL or not REDIS_TOKEN:
        return None
    try:
        _redis = Redis(url=REDIS_URL, token=REDIS_TOKEN)
        return _redis
    except Exception as e:
        print(f"Redis init error: {e}")
        return None


def cache_set(key: str, value: str, expire: int = 3600) -> bool:
    """Store value in cache. Returns False silently if Redis unavailable."""
    try:
        client = _get_redis()
        if client is None:
            return False
        client.set(key, value, ex=expire)
        return True
    except Exception as e:
        print(f"Cache set error: {e}")
        return False


def cache_get(key: str) -> str | None:
    """Get value from cache. Returns None silently if Redis unavailable."""
    try:
        client = _get_redis()
        if client is None:
            return None
        return client.get(key)
    except Exception as e:
        print(f"Cache get error: {e}")
        return None


def cache_delete(key: str) -> bool:
    """Delete from cache. Returns False silently if Redis unavailable."""
    try:
        client = _get_redis()
        if client is None:
            return False
        client.delete(key)
        return True
    except Exception as e:
        print(f"Cache delete error: {e}")
        return False