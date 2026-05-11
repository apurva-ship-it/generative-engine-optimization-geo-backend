import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import status
from httpx import AsyncClient, ASGITransport

from backend.main import app

_REQUIRED_KEYS = {"title", "strategyTag", "description", "prompt"}


@pytest.mark.asyncio
async def test_generate_prompts_returns_200_with_8_items():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        response = await ac.post("/api/generate-prompts", json={"topic": "oncology"})
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "prompts" in body
    assert len(body["prompts"]) == 8


@pytest.mark.asyncio
async def test_generate_prompts_items_have_required_fields():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        response = await ac.post("/api/generate-prompts", json={"topic": "cardiology"})
    assert response.status_code == status.HTTP_200_OK
    for item in response.json()["prompts"]:
        assert set(item.keys()) >= _REQUIRED_KEYS
        for key in _REQUIRED_KEYS:
            assert isinstance(item[key], str) and len(item[key]) > 0


@pytest.mark.asyncio
async def test_generate_prompts_empty_topic_returns_400():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        response = await ac.post("/api/generate-prompts", json={"topic": ""})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_generate_prompts_missing_topic_returns_400():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        response = await ac.post("/api/generate-prompts", json={})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_generate_prompts_non_json_body_returns_400():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        response = await ac.post(
            "/api/generate-prompts",
            content=b"not json",
            headers={"content-type": "application/json"},
        )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_generate_prompts_with_claude_api_parses_response():
    claude_items = [
        {
            "title": f"Title {i}",
            "strategyTag": f"tag-{i}",
            "description": f"Desc {i}",
            "prompt": f"Prompt {i}",
        }
        for i in range(8)
    ]
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"content": [{"text": json.dumps(claude_items)}]}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("backend.routers.generate_prompts.os.getenv", return_value="test-key"),
        patch("backend.routers.generate_prompts.httpx.AsyncClient", return_value=mock_client),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
            response = await ac.post("/api/generate-prompts", json={"topic": "neurology"})

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert len(body["prompts"]) == 8
    assert body["prompts"][0]["title"] == "Title 0"


@pytest.mark.asyncio
async def test_generate_prompts_claude_api_failure_falls_back_to_stubs():
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.HTTPError("connection failed"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("backend.routers.generate_prompts.os.getenv", return_value="test-key"),
        patch("backend.routers.generate_prompts.httpx.AsyncClient", return_value=mock_client),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
            response = await ac.post("/api/generate-prompts", json={"topic": "radiology"})

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["prompts"]) == 8


@pytest.mark.asyncio
async def test_generate_prompts_claude_returns_partial_fills_to_8():
    """When Claude returns fewer than 8 valid items, the rest are filled with stubs."""
    partial = [
        {"title": "T", "strategyTag": "s", "description": "d", "prompt": "p"}
        for _ in range(3)
    ]
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"content": [{"text": json.dumps(partial)}]}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("backend.routers.generate_prompts.os.getenv", return_value="test-key"),
        patch("backend.routers.generate_prompts.httpx.AsyncClient", return_value=mock_client),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
            response = await ac.post("/api/generate-prompts", json={"topic": "immunology"})

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["prompts"]) == 8


@pytest.mark.asyncio
async def test_generate_prompts_claude_returns_more_than_8_truncates():
    """When Claude returns more than 8 items, response is truncated to 8."""
    excess = [
        {"title": f"T{i}", "strategyTag": f"s{i}", "description": f"d{i}", "prompt": f"p{i}"}
        for i in range(12)
    ]
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"content": [{"text": json.dumps(excess)}]}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("backend.routers.generate_prompts.os.getenv", return_value="test-key"),
        patch("backend.routers.generate_prompts.httpx.AsyncClient", return_value=mock_client),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
            response = await ac.post("/api/generate-prompts", json={"topic": "hematology"})

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["prompts"]) == 8
