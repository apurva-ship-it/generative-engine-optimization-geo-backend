import pytest
from httpx import AsyncClient
from fastapi import status
from backend.main import app

@pytest.mark.asyncio
async def test_register_returns_201():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.post(
            "/v1/auth/register",
            data={"username": "alice", "password": "secret", "grant_type": "password"},
        )
    assert response.status_code == status.HTTP_201_CREATED

@pytest.mark.asyncio
async def test_login_sets_cookie():
    # Register first
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        await ac.post(
            "/v1/auth/register",
            data={"username": "bob", "password": "pw", "grant_type": "password"},
        )
        response = await ac.post(
            "/v1/auth/login",
            data={"username": "bob", "password": "pw", "grant_type": "password"},
        )
    assert response.status_code == status.HTTP_200_OK
    # Check cookie attributes
    cookie = response.cookies.get("refresh_token")
    assert cookie is not None
    # httpx does not expose SameSite directly, check header
    set_cookie = response.headers.get("set-cookie")
    assert set_cookie is not None
    assert "HttpOnly" in set_cookie
    assert "SameSite=strict" in set_cookie.lower()

@pytest.mark.asyncio
async def test_refresh_rotates_token():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        # register and login
        await ac.post(
            "/v1/auth/register",
            data={"username": "carol", "password": "pw", "grant_type": "password"},
        )
        login_resp = await ac.post(
            "/v1/auth/login",
            data={"username": "carol", "password": "pw", "grant_type": "password"},
        )
        old_refresh = login_resp.cookies.get("refresh_token")
        # refresh
        refresh_resp = await ac.post("/v1/auth/refresh")
    assert refresh_resp.status_code == status.HTTP_200_OK
    new_refresh = refresh_resp.cookies.get("refresh_token")
    assert new_refresh is not None and new_refresh != old_refresh
    # old token should be revoked, trying again fails
    async with AsyncClient(app=app, base_url="http://testserver", cookies={"refresh_token": old_refresh}) as ac2:
        bad_resp = await ac2.post("/v1/auth/refresh")
    assert bad_resp.status_code == status.HTTP_401_UNAUTHORIZED
