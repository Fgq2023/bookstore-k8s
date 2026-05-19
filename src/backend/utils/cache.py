"""Distributed Redis cache with in-memory fallback."""
import os
import time
import logging

logger = logging.getLogger('bookstore')

# In-memory fallback cache
_cache = {}

# Lazy Redis connection
_redis_client = None


def _get_redis():
    """Return Redis client if available, else None."""
    global _redis_client
    if _redis_client is not None:
        try:
            _redis_client.ping()
            return _redis_client
        except Exception:
            logger.warning("Redis connection lost, falling back to in-memory cache")
            _redis_client = None
            return None

    redis_url = os.getenv('REDIS_URL')
    if not redis_url:
        return None

    try:
        import redis as redis_lib
        _redis_client = redis_lib.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2, decode_responses=False)
        _redis_client.ping()
        logger.info("Redis cache connected")
        return _redis_client
    except ImportError:
        logger.warning("redis package not installed, using in-memory cache")
        return None
    except Exception as e:
        logger.warning(f"Redis connection failed ({e}), using in-memory cache")
        return None


def cache_get(key):
    r = _get_redis()
    if r:
        try:
            data = r.get(key)
            if data:
                import pickle
                return pickle.loads(data)
        except Exception as e:
            logger.warning(f"Redis cache_get failed: {e}")
    # Fallback to memory
    entry = _cache.get(key)
    if entry and time.time() < entry['expires']:
        return entry['value']
    if key in _cache:
        del _cache[key]
    return None


def cache_set(key, value, ttl_seconds=60):
    r = _get_redis()
    if r:
        try:
            import pickle
            r.setex(key, ttl_seconds, pickle.dumps(value))
            return
        except Exception as e:
            logger.warning(f"Redis cache_set failed: {e}")
    # Fallback to memory
    _cache[key] = {'value': value, 'expires': time.time() + ttl_seconds}


def cache_delete(key):
    r = _get_redis()
    if r:
        try:
            r.delete(key)
        except Exception as e:
            logger.warning(f"Redis cache_delete failed: {e}")
    _cache.pop(key, None)


def cache_clear_prefix(prefix):
    """Remove all cache entries whose keys start with the given prefix."""
    global _cache
    r = _get_redis()
    if r:
        try:
            # Use SCAN to find keys safely (avoids KEYS in production)
            for key in r.scan_iter(match=f"{prefix}*"):
                r.delete(key)
        except Exception as e:
            logger.warning(f"Redis cache_clear_prefix failed: {e}")
    keys_to_remove = [k for k in _cache if k.startswith(prefix)]
    for k in keys_to_remove:
        del _cache[k]
