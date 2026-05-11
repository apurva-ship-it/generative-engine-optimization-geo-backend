"""Integration tests — auth + file operations in realistic user flows."""
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status
from backend.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
async def authed_client():
    """Client with a logged-in session cookie."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        await ac.post("/v1/auth/register", json={"username": "user1", "password": "pass123"})
        await ac.post("/v1/auth/login", json={"username": "user1", "password": "pass123"})
        yield ac


# ── Auth → /me flow ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_login_me_full_flow(client):
    reg = await client.post("/v1/auth/register", json={"username": "jane", "password": "pw1234"})
    assert reg.status_code == 201

    login = await client.post("/v1/auth/login", json={"username": "jane", "password": "pw1234"})
    assert login.status_code == 200
    assert "access_token" in login.cookies

    me = await client.get("/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["username"] == "jane"


@pytest.mark.asyncio
async def test_unauthenticated_me_blocked(client):
    resp = await client.get("/v1/auth/me")
    assert resp.status_code == 401


# ── Token rotation flow ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_token_rotation_revokes_old_refresh(client):
    await client.post("/v1/auth/register", json={"username": "bob", "password": "pw"})
    login = await client.post("/v1/auth/login", json={"username": "bob", "password": "pw"})
    old_rt = login.cookies.get("refresh_token")

    # Rotate
    refresh1 = await client.post("/v1/auth/refresh")
    assert refresh1.status_code == 200

    # Old refresh token is now revoked — use a fresh client with only the old token
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
        cookies={"refresh_token": old_rt},
    ) as stale:
        bad = await stale.post("/v1/auth/refresh")
    assert bad.status_code == 401


# ── Logout invalidation ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_logout_prevents_me_access(client):
    await client.post("/v1/auth/register", json={"username": "carol", "password": "pw"})
    await client.post("/v1/auth/login", json={"username": "carol", "password": "pw"})

    # Logged in — can access /me
    me = await client.get("/v1/auth/me")
    assert me.status_code == 200

    await client.post("/v1/auth/logout")

    # After logout access_token cookie gone → 401
    resp = await client.get("/v1/auth/me")
    assert resp.status_code == 401


# ── File operations after auth ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_upload_then_list(authed_client):
    upload = await authed_client.post("/v1/files/upload")
    assert upload.status_code == 200
    assert "presigned_url" in upload.json()

    files = await authed_client.get("/v1/files/")
    assert files.status_code == 200
    assert isinstance(files.json(), list)


@pytest.mark.asyncio
async def test_delete_then_list_excludes_file(authed_client):
    del_resp = await authed_client.delete("/v1/files/1")
    assert del_resp.status_code == 204

    list_resp = await authed_client.get("/v1/files/")
    assert "file1.txt" not in list_resp.json()
    assert "file2.txt" in list_resp.json()


@pytest.mark.asyncio
async def test_edit_file_content(authed_client):
    resp = await authed_client.put("/v1/files/1/content")
    assert resp.status_code == 200
    assert "version_id" in resp.json()


# ── CORS headers ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cors_allowed_origin(client):
    resp = await client.get(
        "/v1/files/",
        headers={"Origin": "http://localhost:5173"},
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"


@pytest.mark.asyncio
async def test_cors_blocked_for_unknown_origin(client):
    resp = await client.get(
        "/v1/files/",
        headers={"Origin": "http://evil.example.com"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_preflight_returns_cors_headers(client):
    resp = await client.options(
        "/v1/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert resp.status_code in (200, 204)
    assert "access-control-allow-origin" in resp.headers
