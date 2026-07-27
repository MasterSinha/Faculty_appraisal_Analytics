import json
import logging
import os
import threading
import time
from typing import Any, Optional, Tuple

from app.core.config import get_settings

logger = logging.getLogger("analytics.cache")

_cache_store: dict[str, Tuple[Any, float]] = {}
_cache_lock = threading.RLock()
_cache_stats = {
    "hits": 0,
    "misses": 0,
    "keys_created": 0,
}
_health_stats = {
    "slowest_recent_endpoint": "",
    "slowest_recent_ms": 0.0,
    "last_materialized_view_refresh": "",
}

# Optional Redis connection
_redis_client = None
_redis_initialized = False


def _get_redis():
    global _redis_client, _redis_initialized
    if _redis_initialized:
        return _redis_client

    _redis_initialized = True
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            import redis
            _redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
            _redis_client.ping()
            logger.info("Successfully connected to Redis cache: %s", redis_url)
        except Exception as e:
            logger.warning("Failed to connect to Redis cache (%s). Falling back to in-memory TTL cache.", e)
            _redis_client = None
    return _redis_client


def build_cache_key(prefix: str, filters: dict[str, Any]) -> str:
    """Generate deterministic cache key based on route prefix and sorted filter parameters."""
    normalized_parts = []
    if filters:
        for k in sorted(filters.keys()):
            val = filters[k]
            if val is not None and str(val).strip() != "":
                normalized_parts.append(f"{k}={str(val).strip().lower()}")
    query_str = "&".join(normalized_parts) if normalized_parts else "all"
    return f"analytics:{prefix}:{query_str}"


def get_cache(key: str) -> Tuple[bool, Any]:
    """Retrieve value from cache. Returns (is_hit, data)."""
    # 1. Try Redis if available
    r = _get_redis()
    if r:
        try:
            cached_val = r.get(key)
            if cached_val is not None:
                _cache_stats["hits"] += 1
                return True, json.loads(cached_val)
        except Exception as e:
            logger.warning("Redis read error for key %s: %s", key, e)

    # 2. In-memory TTL fallback
    now = time.time()
    with _cache_lock:
        if key in _cache_store:
            data, expire_time = _cache_store[key]
            if expire_time > now:
                _cache_stats["hits"] += 1
                return True, data
            else:
                # Expired
                del _cache_store[key]

        _cache_stats["misses"] += 1
        return False, None


def set_cache(key: str, data: Any, ttl_seconds: int = 60) -> None:
    """Store value in cache with TTL."""
    # 1. Try Redis if available
    r = _get_redis()
    if r:
        try:
            r.setex(key, ttl_seconds, json.dumps(data, default=str))
        except Exception as e:
            logger.warning("Redis write error for key %s: %s", key, e)

    # 2. In-memory TTL store
    now = time.time()
    expire_time = now + ttl_seconds
    with _cache_lock:
        _cache_store[key] = (data, expire_time)
        _cache_stats["keys_created"] += 1


def clear_cache(prefix: Optional[str] = None) -> int:
    """Clear cached entries matching prefix or all if prefix is None."""
    count = 0
    r = _get_redis()
    if r:
        try:
            pattern = f"analytics:{prefix}*" if prefix else "analytics:*"
            keys = r.keys(pattern)
            if keys:
                r.delete(*keys)
                count += len(keys)
        except Exception as e:
            logger.warning("Redis clear error: %s", e)

    with _cache_lock:
        now = time.time()
        keys_to_delete = []
        for k in list(_cache_store.keys()):
            if prefix is None or k.startswith(f"analytics:{prefix}"):
                keys_to_delete.append(k)
        for k in keys_to_delete:
            del _cache_store[k]
            count += 1

    return count


def get_cache_stats() -> dict[str, Any]:
    """Return cache stats and active key count."""
    now = time.time()
    with _cache_lock:
        active_keys = sum(1 for _, exp in _cache_store.values() if exp > now)
        return {
            "hits": _cache_stats["hits"],
            "misses": _cache_stats["misses"],
            "active_in_memory_keys": active_keys,
            "total_keys_created": _cache_stats["keys_created"],
            "redis_enabled": _redis_client is not None,
        }


def record_endpoint_timing(endpoint: str, duration_ms: float) -> None:
    """Record timing of endpoint for health endpoint tracking."""
    if duration_ms > _health_stats["slowest_recent_ms"]:
        _health_stats["slowest_recent_ms"] = duration_ms
        _health_stats["slowest_recent_endpoint"] = f"{endpoint} ({duration_ms:.1f}ms)"


def update_last_refresh_timestamp(ts_str: str) -> None:
    """Update last materialized view refresh timestamp."""
    _health_stats["last_materialized_view_refresh"] = ts_str


def get_health_stats() -> dict[str, Any]:
    """Return recorded health stats."""
    return dict(_health_stats)
