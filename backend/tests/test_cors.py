import os
import pytest
from httpx import AsyncClient
from fastapi import status

from backend.main import app
from backend.config import Settings

@pytest.fixture(scope="function", autouse=True)
def set_allowed_origins(monkeypatch):
    # Set allowed origins for test
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://allowed.com")
    # Reload settings module to pick up env change
    import importlib
    import backend.config as config_mod
    importlib.reload(config_mod)
    yield
    # Cleanup
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    importlib.reload(config_mod)

@pytest.mark.asyncio
async def test_allowed_origin():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        headers = {"origin": "http://allowed.com"}
        response = await client.options("/nonexistent", headers=headers)
        # Should not be forbidden
        assert response.status_code != status.HTTP_403_FORBIDDEN
        # CORS header should be present
        assert response.headers.get("access-control-allow-origin") == "http://allowed.com"

@pytest.mark.asyncio
async def test_disallowed_origin():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        headers = {"origin": "http://evil.com"}
        response = await client.options("/nonexistent", headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["detail"] == "Origin not allowed"
