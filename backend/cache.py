"""
cache.py
----------
Deliverable 8: Caching Layer (Redis).

Caches expensive, frequently-repeated computations - roadmaps,
recommendations, resume scores - so 100 users asking for the same
career's roadmap doesn't mean 100 identical recalculations.

GRACEFUL DEGRADATION: if Redis isn't running (common in dev, or if it
crashes in production), every cache call fails safely and the app just
recomputes normally - caching is a performance optimization, never a
hard dependency. You'll see one clear warning at startup, not a crash.
"""

from __future__ import annotations

import hashlib
import json
import os
from functools import wraps
from typing import Optional

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DEFAULT_TTL_SECONDS = 60 * 60  # 1 hour

try:
    _redis_client = redis.from_url(REDIS_URL, socket_connect_timeout=2, decode_responses=True)
    _redis_client.ping()
    REDIS_AVAILABLE = True
    print(f"[cache] Connected to Redis at {REDIS_URL} - caching is active.")
except Exception as e:
    _redis_client = None
    REDIS_AVAILABLE = False
    print(f"[cache] Redis not reachable ({e}) - running without caching. Everything still works, just recomputes every time.")


def _make_cache_key(prefix: str, *args, **kwargs) -> str:
    raw = f"{prefix}:{args}:{sorted(kwargs.items())}"
    digest = hashlib.md5(raw.encode()).hexdigest()
    return f"career_advisor:{prefix}:{digest}"


def get_cached(key: str) -> Optional[dict]:
    if not REDIS_AVAILABLE:
        return None
    try:
        raw = _redis_client.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None  # any Redis hiccup -> treat as a cache miss, never crash the request


def set_cached(key: str, value, ttl: int = DEFAULT_TTL_SECONDS) -> None:
    if not REDIS_AVAILABLE:
        return
    try:
        _redis_client.setex(key, ttl, json.dumps(value))
    except Exception:
        pass  # caching failures should never break the actual response


def cached(prefix: str, ttl: int = DEFAULT_TTL_SECONDS):
    """
    Decorator: caches a function's return value in Redis, keyed by its
    arguments. Use on pure/deterministic functions only (same input should
    always produce the same output) - e.g. get_roadmap(), not anything
    involving live user state that changes between calls.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = _make_cache_key(prefix, *args, **kwargs)
            hit = get_cached(key)
            if hit is not None:
                return hit
            result = func(*args, **kwargs)
            set_cached(key, result, ttl)
            return result
        return wrapper
    return decorator


def invalidate_prefix(prefix: str) -> int:
    """Clears all cached entries under a prefix (e.g. after data changes)."""
    if not REDIS_AVAILABLE:
        return 0
    try:
        keys = _redis_client.keys(f"career_advisor:{prefix}:*")
        if keys:
            return _redis_client.delete(*keys)
        return 0
    except Exception:
        return 0