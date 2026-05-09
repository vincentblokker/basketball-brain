"""In-process per-IP rate-limit for /query.

Tracks rolling-window hit timestamps per client IP. Behind a reverse
proxy (Caddy on host), prefers X-Forwarded-For; otherwise uses scope's
client address. Disabled when limits set to 0.

Limits are per worker process — with N uvicorn workers a hot client
gets up to N×limit. Acceptable for our 2-worker setup; switch to a
shared store (Redis) only if abuse becomes real.
"""
from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.config import settings

PROTECTED_PATHS = ("/query",)


class _Window:
    __slots__ = ("hits",)

    def __init__(self) -> None:
        self.hits: list[float] = []

    def prune(self, cutoff: float) -> None:
        # Drop timestamps older than cutoff (inplace).
        i = 0
        for ts in self.hits:
            if ts >= cutoff:
                break
            i += 1
        if i:
            del self.hits[:i]

    def count_since(self, cutoff: float) -> int:
        self.prune(cutoff)
        return len(self.hits)

    def add(self, ts: float) -> None:
        self.hits.append(ts)


class RateLimiter:
    """Per-IP rolling-window counter."""

    def __init__(self, per_hour: int, per_day: int) -> None:
        self.per_hour = per_hour
        self.per_day = per_day
        self._windows: dict[str, _Window] = {}

    def check(self, ip: str) -> tuple[bool, dict[str, int]]:
        """Returns (allowed, headers_dict). If allowed=False, headers carry
        Retry-After + X-RateLimit-Reset; if True, also returns Remaining."""
        now = time.time()
        win = self._windows.setdefault(ip, _Window())
        day_cut = now - 86400
        hour_cut = now - 3600
        day_count = win.count_since(day_cut)
        hour_count = sum(1 for t in win.hits if t >= hour_cut)

        if self.per_day > 0 and day_count >= self.per_day:
            oldest = min(t for t in win.hits if t >= day_cut)
            retry_after = int(oldest + 86400 - now) + 1
            return False, {
                "X-RateLimit-Limit-Day": self.per_day,
                "X-RateLimit-Remaining-Day": 0,
                "Retry-After": retry_after,
            }
        if self.per_hour > 0 and hour_count >= self.per_hour:
            oldest = min(t for t in win.hits if t >= hour_cut)
            retry_after = int(oldest + 3600 - now) + 1
            return False, {
                "X-RateLimit-Limit-Hour": self.per_hour,
                "X-RateLimit-Remaining-Hour": 0,
                "Retry-After": retry_after,
            }

        win.add(now)
        return True, {
            "X-RateLimit-Limit-Day": self.per_day,
            "X-RateLimit-Remaining-Day": max(0, self.per_day - day_count - 1),
            "X-RateLimit-Limit-Hour": self.per_hour,
            "X-RateLimit-Remaining-Hour": max(0, self.per_hour - hour_count - 1),
        }


_limiter: RateLimiter | None = None


def _get_limiter() -> RateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = RateLimiter(
            per_hour=settings.rate_limit_per_hour,
            per_day=settings.rate_limit_per_day,
        )
    return _limiter


def _client_ip(request: Request) -> str:
    if settings.rate_limit_trust_forwarded:
        fwd = request.headers.get("x-forwarded-for", "")
        if fwd:
            # First IP in the comma-list is the real client.
            return fwd.split(",")[0].strip()
    client = request.client
    return client.host if client else "unknown"


class RateLimitMiddleware:
    """ASGI middleware — applies rate-limit only to PROTECTED_PATHS."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path = scope.get("path", "")
        if not any(path == p or path.startswith(p + "/") for p in PROTECTED_PATHS):
            await self.app(scope, receive, send)
            return
        # Skip if both limits disabled
        if settings.rate_limit_per_day <= 0 and settings.rate_limit_per_hour <= 0:
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        ip = _client_ip(request)
        allowed, hdrs = _get_limiter().check(ip)
        if not allowed:
            payload = {
                "error": "rate_limited",
                "message": (
                    "Je hebt het maximum aantal vragen voor nu bereikt. "
                    "Probeer het later opnieuw."
                ),
                **{k.lower(): v for k, v in hdrs.items()},
            }
            response = JSONResponse(
                content=payload,
                status_code=429,
                headers={k: str(v) for k, v in hdrs.items()},
            )
            await response(scope, receive, send)
            return

        # Inject headers on the response — wrap send.
        async def wrapped_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                # Mutate headers in-place to add rate-limit info.
                existing = list(message.get("headers", []))
                for k, v in hdrs.items():
                    existing.append((k.encode("latin-1"), str(v).encode("latin-1")))
                message["headers"] = existing
            await send(message)

        await self.app(scope, receive, wrapped_send)


# Re-export for convenience
__all__ = ["RateLimitMiddleware"]


# Type-friendly factory used by main.py
RateLimitMiddlewareCallable = Callable[[ASGIApp], Awaitable[Any]]
