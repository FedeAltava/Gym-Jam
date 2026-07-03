"""In-memory sliding-window rate limiter for FastAPI.

Per-IP limits:
  - /auth/login:    5 attempts per 60 seconds
  - /auth/register: 10 attempts per 60 seconds
  - /auth/refresh:  30 attempts per 60 seconds

Returns HTTP 429 when the limit is exceeded.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request, status


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


# Module-level limiter instances — one per endpoint group.
login_limiter = SlidingWindowRateLimiter(max_calls=5, window_seconds=60)
register_limiter = SlidingWindowRateLimiter(max_calls=10, window_seconds=60)
refresh_limiter = SlidingWindowRateLimiter(max_calls=30, window_seconds=60)
logout_limiter = SlidingWindowRateLimiter(max_calls=30, window_seconds=60)
