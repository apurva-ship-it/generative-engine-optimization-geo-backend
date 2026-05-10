"""FastAPI application factory with rate limiting middleware.

This file sets up the FastAPI instance, attaches the
:class:`RateLimitMiddleware` and includes the application routers.
"""

from fastapi import FastAPI

from .routers.files import router as files_router
from .middleware.rate_limit import RateLimitMiddleware

# Instantiate the FastAPI application
app = FastAPI(title="File Management API")

# Add rate‑limiting middleware
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(files_router)

# The application can now be run with: uvicorn backend.main:app
