"""In-memory TTL cache helpers."""
import time

_cache = {}


def cache_get(key):
    entry = _cache.get(key)
    if entry and time.time() < entry['expires']:
        return entry['value']
    if key in _cache:
        del _cache[key]
    return None


def cache_set(key, value, ttl_seconds=60):
    _cache[key] = {'value': value, 'expires': time.time() + ttl_seconds}


def cache_delete(key):
    _cache.pop(key, None)
