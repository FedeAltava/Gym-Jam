"""Sliding-window rate limiters for FastAPI.

Per-IP limits:
  - /auth/login:    5 attempts per 60 seconds
  - /auth/register: 10 attempts per 60 seconds
  - /auth/refresh:  30 attempts per 60 seconds

Returns HTTP 429 when the limit is exceeded.

Two implementations:
  - SlidingWindowRateLimiter: in-process (per-worker) state. Used in tests
    and single-worker development where Redis is not available.
  - RedisRateLimiter: shared state across all uvicorn workers via Redis
    sorted sets. Selected automatically when REDIS_URL is configured.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

import redis.asyncio as aioredis
from fastapi import HTTPException, Request, status

from backend.src.infrastructure.config import settings


class SlidingWindowRateLimiter:
    """Thread-safe, in-memory sliding-window rate limiter."""

    def __init__(self, max_calls: int, window_seconds: int) -> None:
        self._max_calls = max_calls
        self._window_seconds = window_seconds
        self._records: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _get_client_ip(self, request: Request) -> str:
        # X-Forwarded-For is deliberately IGNORED: its first entry is
        # client-controlled (nginx appends the real IP after any
        # client-supplied values), so keying on it allows a spoof bypass.
        # X-Real-IP is set by our nginx reverse proxy from $remote_addr
        # (a single trusted hop), so it is safe to key on.
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        if request.client:
            return request.client.host
        return "unknown"

    def is_allowed(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self._window_seconds
        with self._lock:
            timestamps = self._records[key]
            # Evict entries outside the window
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()
            if len(timestamps) >= self._max_calls:
                return False
            timestamps.append(now)
            return True

    def reset(self, key: str | None = None) -> None:
        """Reset state — used in tests to clear limiter between test runs."""
        with self._lock:
            if key is None:
                self._records.clear()
            else:
                self._records.pop(key, None)

    def dependency(self, request: Request) -> None:
        """FastAPI dependency that enforces the rate limit."""
        ip = self._get_client_ip(request)
        if not self.is_allowed(ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
            )


_SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window_start = tonumber(ARGV[2])
local max_calls = tonumber(ARGV[3])
local expire = tonumber(ARGV[4])
redis.call('ZREMRANGEBYSCORE', key, 0, window_start)
local count = redis.call('ZCARD', key)
if count >= max_calls then
    return 0
end
local seq = redis.call('INCR', key .. ':seq')
redis.call('EXPIRE', key .. ':seq', expire)
redis.call('ZADD', key, now, tostring(now) .. ':' .. seq)
redis.call('EXPIRE', key, expire)
return 1
"""


class RedisRateLimiter:
    """Redis-backed sliding-window rate limiter. Shared across workers.

    Uses a Redis sorted set per (prefix, client-IP) key. The check-and-add
    is executed as a single atomic Lua script, eliminating the TOCTOU race
    that would otherwise allow concurrent requests to slip past the limit.
    """

    def __init__(self, max_calls: int, window_seconds: int, key_prefix: str) -> None:
        self._max_calls = max_calls
        self._window_seconds = window_seconds
        self._key_prefix = key_prefix
        self._redis: aioredis.Redis | None = None

    def _get_redis(self) -> aioredis.Redis:
        # Lazily create the client so importing this module never opens a
        # connection (relevant for tests and tooling that import the app).
        if self._redis is None:
            self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    def _get_client_ip(self, request: Request) -> str:
        # Same trust model as SlidingWindowRateLimiter: X-Forwarded-For is
        # client-spoofable, X-Real-IP is set by our nginx from $remote_addr.
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        if request.client:
            return request.client.host
        return "unknown"

    async def is_allowed(self, key: str) -> bool:
        r = self._get_redis()
        full_key = f"rl:{self._key_prefix}:{key}"
        now = time.time()
        window_start = now - self._window_seconds
        # Single atomic Lua script: prune + count + conditionally add.
        # Eliminates the TOCTOU gap between the pipeline read and the zadd.
        result = await r.eval(
            _SLIDING_WINDOW_LUA,
            1,
            full_key,
            str(now),
            str(window_start),
            str(self._max_calls),
            str(self._window_seconds * 2),
        )
        return bool(result)

    def reset(self, key: str | None = None) -> None:
        """No-op — Redis keys expire on their own; tests use the in-memory limiter."""

    async def dependency(self, request: Request) -> None:
        """FastAPI dependency that enforces the rate limit."""
        ip = self._get_client_ip(request)
        if not await self.is_allowed(ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
            )


def _make_limiter(
    max_calls: int, window_seconds: int, key_prefix: str
) -> SlidingWindowRateLimiter | RedisRateLimiter:
    """Return a Redis-backed limiter when REDIS_URL is configured, else in-memory.

    Tests and single-worker dev setups do not set REDIS_URL, so they keep the
    in-process limiter (with its synchronous `dependency` and working `reset`).
    """
    if settings.redis_url:
        return RedisRateLimiter(
            max_calls=max_calls, window_seconds=window_seconds, key_prefix=key_prefix
        )
    return SlidingWindowRateLimiter(max_calls=max_calls, window_seconds=window_seconds)


# Module-level limiter instances — one per endpoint group.
login_limiter = _make_limiter(5, 60, "login")
register_limiter = _make_limiter(10, 60, "register")
refresh_limiter = _make_limiter(30, 60, "refresh")
logout_limiter = _make_limiter(30, 60, "logout")
forgot_password_limiter = _make_limiter(3, 60, "forgot_password")
reset_password_limiter = _make_limiter(5, 60, "reset_password")
change_password_limiter = _make_limiter(5, 60, "change_password")
