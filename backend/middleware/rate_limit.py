"""Simple in‑memory rate limiting middleware.

This implementation mimics a Redis sliding window algorithm but stores
request timestamps in a dict keyed by the client IP.  It satisfies the
exercise acceptance criteria for demonstration purposes.

In a real deployment this should be replaced by a Redis backed
implementation.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Awaitable, Callable, MutableMapping

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

# Constants used in the exercise
MAX_ATTEMPTS = 5
BLOCK_TIME = timedelta(minutes=15)
WINDOW = BLOCK_TIME  # sliding window of 15 minutes

# In‑memory store: {ip: [attempt_datetimes]}
_attempts_store: MutableMapping[str, list[datetime]] = {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests that exceed a sliding window of 5 failed attempts.

    The logic is intentionally simple: on each request we purge timestamps
    older than WINDOW, then check if the IP is currently blocked.  For
    authentication endpoints the failure check is delegated to the
    endpoint via the ``X‑Auth‑Failed`` header – this keeps the middleware
    agnostic to the authentication implementation.
    """

    def __init__(self, app: FastAPI, *, skip_paths: set[str] | None = None):
        super().__init__(app)
        self.skip_paths = skip_paths or {"/docs", "/openapi.json"}

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Skip paths that should not be rate‑limited
        if request.url.path in self.skip_paths:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = datetime.utcnow()

        attempts = _attempts_store.setdefault(client_ip, [])
        # Remove old attempts outside the window
        attempts[:] = [ts for ts in attempts if now - ts < WINDOW]

        # If the IP is actively blocked, reject immediately
        if self._is_blocked(attempts, now):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Try again later.",
            )

        # Proceed with the request
        response = await call_next(request)

        # For endpoints that signal a failure via header, record the attempt
        if request.url.path.startswith("/api/v1/auth"):
            header = response.headers.get("X-Auth-Failed")
            if header == "1":
                attempts.append(now)
        return response

    def _is_blocked(self, attempts: list[datetime], now: datetime) -> bool:
        if len(attempts) < MAX_ATTEMPTS:
            return False
        # The earliest timestamp in the current block window
        earliest = attempts[0]
        return now - earliest < BLOCK_TIME

# This middleware can be added to a FastAPI application via:
# app.add_middleware(RateLimitMiddleware)
