"""FastAPI application factory with CORS and rate limiting middleware.

Sets up FastAPI, applies RateLimitMiddleware, and enforces CORS based on
ALLOWED_ORIGINS environment variable.
"""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import Response, JSONResponse

from .routers.files import router as files_router
from .routers.auth import router as auth_router
from .middleware.rate_limit import RateLimitMiddleware
from .config import Settings

app = FastAPI(title="File Management API")

# Load configuration
settings = Settings()

@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin")
    # Allow requests without Origin (e.g., server‑to‑server)
    if origin and origin not in settings.allowed_origins:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Origin not allowed")

    # Handle preflight requests
    if request.method == "OPTIONS":
        response = JSONResponse(content={})
    else:
        response: Response = await call_next(request)

    # Attach CORS headers for allowed origins
    if origin and origin in settings.allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Add rate‑limiting middleware
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(files_router)
app.include_router(auth_router)

# The application can now be run with: uvicorn backend.main:app
