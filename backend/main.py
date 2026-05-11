"""FastAPI application factory with CORS and rate limiting middleware."""
from fastapi import FastAPI, Request, status
from fastapi.responses import Response, JSONResponse
from .routers.files import router as files_router
from .routers.auth import router as auth_router
from .middleware.rate_limit import RateLimitMiddleware
from .config import Settings

app = FastAPI(title="File Management API")
settings = Settings()

@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin")
    if origin and origin not in settings.allowed_origins:
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "Origin not allowed"})
    if request.method == "OPTIONS":
        response = JSONResponse(content={})
    else:
        response: Response = await call_next(request)
    if origin and origin in settings.allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response

app.add_middleware(RateLimitMiddleware)
app.include_router(files_router)
app.include_router(auth_router)
