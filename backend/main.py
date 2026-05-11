"""FastAPI application factory with CORS and optional HTTPS enforcement middleware."""
from fastapi import FastAPI, Request, status
from fastapi.responses import Response, JSONResponse
from .routers.files import router as files_router
from .routers.auth import router as auth_router
from .middleware.rate_limit import RateLimitMiddleware
from .config import Settings

app = FastAPI(title="File Management API")
settings = Settings()

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    # Optional HTTPS enforcement: only enforce in production mode if env var PRODUCTION=True
    if getattr(settings, "production", False):
        if request.url.scheme != "https":
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "HTTPS required"})
    # CORS handling
    origin = request.headers.get("origin")
    if origin and origin not in settings.allowed_origins:
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "Origin not allowed"})
    # Handle preflight requests
    if request.method == "OPTIONS":
        response = JSONResponse(content={})
        response.headers["Access-Control-Allow-Origin"] = origin or "*"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Authorization,Content-Type"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response
    response: Response = await call_next(request)
    # Add CORS headers to normal responses
    if origin and origin in settings.allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Authorization,Content-Type"
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

app.add_middleware(RateLimitMiddleware)
app.include_router(files_router)
app.include_router(auth_router)
