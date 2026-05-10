"""Application level dependencies.

This module provides a few helpers that can be used in routes:

* ``get_client_ip`` – resolves the IP address of the incoming request.  It
  ensures that the middleware has a deterministic key to use for rate
  limiting.
* ``get_remaining_attempts`` – exposes the number of failed attempts left
  for the current IP address.  This is useful when you want to surface
  the remaining quota in a response header or behaviour.

The implementation is intentionally simple and uses the in‑memory store
defined in :mod:`middleware.rate_limit`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request

from .middleware.rate_limit import _attempts_store, MAX_ATTEMPTS, WINDOW


async def get_client_ip(request: Request) -> str:
    """Return the client IP address.

    Raises a 400 *Unable to determine client IP* if the request has no
    ``client`` information.  The middleware relies on this same key to
    track attempts in :data:`_attempts_store`.
    """
    if not request.client:
        raise HTTPException(status_code=400, detail="Unable to determine client IP")
    return request.client.host


async def get_remaining_attempts(
    client_ip: Annotated[str, Depends(get_client_ip)]
) -> int:
    """Return the number of remaining allowed attempts for the client.

    This helper cleans the store of expired timestamps and computes the
    remaining quota.
    """
    attempts: list[datetime] = _attempts_store.get(client_ip, [])
    now = datetime.utcnow()
    attempts = [ts for ts in attempts if now - ts < WINDOW]
    remaining = max(0, MAX_ATTEMPTS - len(attempts))
    return remaining
