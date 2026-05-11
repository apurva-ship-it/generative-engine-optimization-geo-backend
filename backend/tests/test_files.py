import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status
from backend.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac


@pytest.mark.asyncio
async def test_list_files_returns_initial_set(client):
    resp = await client.get("/v1/files/")
    assert resp.status_code == status.HTTP_200_OK
    assert set(resp.json()) == {"file1.txt", "file2.txt"}


@pytest.mark.asyncio
async def test_list_excludes_deleted_files(client):
    await client.delete("/v1/files/1")
    resp = await client.get("/v1/files/")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == ["file2.txt"]


@pytest.mark.asyncio
async def test_upload_returns_presigned_url(client):
    resp = await client.post("/v1/files/upload")
    assert resp.status_code == status.HTTP_200_OK
    assert "presigned_url" in resp.json()


@pytest.mark.asyncio
async def test_edit_content_returns_version_id(client):
    resp = await client.put("/v1/files/2/content")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json().get("version_id") == 42


@pytest.mark.asyncio
async def test_delete_returns_204(client):
    resp = await client.delete("/v1/files/1")
    assert resp.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_delete_nonexistent_returns_404(client):
    resp = await client.delete("/v1/files/999")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_already_deleted_returns_404(client):
    await client.delete("/v1/files/1")
    resp = await client.delete("/v1/files/1")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_soft_delete_preserves_other_files(client):
    await client.delete("/v1/files/1")
    resp = await client.get("/v1/files/")
    names = resp.json()
    assert "file2.txt" in names
    assert "file1.txt" not in names
