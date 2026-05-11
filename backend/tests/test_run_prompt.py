import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from backend.main import app


@pytest.mark.asyncio
async def test_run_prompt_no_llms_returns_400():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        response = await ac.post("/api/run-prompt", json={"prompt": "test", "selected_llms": []})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_run_prompt_missing_prompt_returns_400():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        response = await ac.post("/api/run-prompt", json={"selected_llms": ["CLAUDE"]})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_run_prompt_empty_prompt_returns_400():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        response = await ac.post("/api/run-prompt", json={"prompt": "", "selected_llms": ["CLAUDE"]})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_run_prompt_missing_selected_llms_returns_400():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        response = await ac.post("/api/run-prompt", json={"prompt": "hello"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_run_prompt_non_json_body_returns_400():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        response = await ac.post(
            "/api/run-prompt",
            content=b"not json",
            headers={"content-type": "application/json"},
        )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_run_prompt_response_has_camel_case_fields():
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"content": [{"type": "text", "text": "Hello from Claude"}]}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("backend.routers.run_prompt.os.getenv", return_value="test-key"),
        patch("backend.routers.run_prompt.httpx.AsyncClient", return_value=mock_client),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
            response = await ac.post("/api/run-prompt", json={"prompt": "test", "selected_llms": ["CLAUDE"]})

    assert response.status_code == status.HTTP_200_OK
    result = response.json()["results"][0]
    assert "llmName" in result
    assert "responseText" in result
    assert "latencyMs" in result
    assert isinstance(result["latencyMs"], int)
    assert result["llmName"] == "CLAUDE"
    assert result["responseText"] == "Hello from Claude"
    assert result["error"] is None


@pytest.mark.asyncio
async def test_run_prompt_openai_response_parsed():
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"choices": [{"message": {"content": "Hello from OpenAI"}}]}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("backend.routers.run_prompt.os.getenv", return_value="test-key"),
        patch("backend.routers.run_prompt.httpx.AsyncClient", return_value=mock_client),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
            response = await ac.post("/api/run-prompt", json={"prompt": "test", "selected_llms": ["OPENAI"]})

    assert response.status_code == status.HTTP_200_OK
    result = response.json()["results"][0]
    assert result["responseText"] == "Hello from OpenAI"


@pytest.mark.asyncio
async def test_run_prompt_cohere_response_parsed():
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"message": {"content": [{"type": "text", "text": "Hello from Cohere"}]}}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("backend.routers.run_prompt.os.getenv", return_value="test-key"),
        patch("backend.routers.run_prompt.httpx.AsyncClient", return_value=mock_client),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
            response = await ac.post("/api/run-prompt", json={"prompt": "test", "selected_llms": ["COHERE"]})

    assert response.status_code == status.HTTP_200_OK
    result = response.json()["results"][0]
    assert result["responseText"] == "Hello from Cohere"


@pytest.mark.asyncio
async def test_run_prompt_unconfigured_llm_returns_error_field():
    with patch("backend.routers.run_prompt.os.getenv", return_value=None):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
            response = await ac.post("/api/run-prompt", json={"prompt": "test", "selected_llms": ["CLAUDE"]})

    assert response.status_code == status.HTTP_200_OK
    result = response.json()["results"][0]
    assert result["error"] is not None
    assert result["responseText"] is None
    assert isinstance(result["latencyMs"], int)


@pytest.mark.asyncio
async def test_run_prompt_unknown_llm_returns_error_field():
    with patch("backend.routers.run_prompt.os.getenv", return_value=None):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
            response = await ac.post("/api/run-prompt", json={"prompt": "test", "selected_llms": ["UNKNOWN_LLM"]})

    assert response.status_code == status.HTTP_200_OK
    result = response.json()["results"][0]
    assert result["error"] is not None


@pytest.mark.asyncio
async def test_run_prompt_timeout_returns_error_field():
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timed out"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("backend.routers.run_prompt.os.getenv", return_value="test-key"),
        patch("backend.routers.run_prompt.httpx.AsyncClient", return_value=mock_client),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
            response = await ac.post("/api/run-prompt", json={"prompt": "test", "selected_llms": ["OPENAI"]})

    assert response.status_code == status.HTTP_200_OK
    result = response.json()["results"][0]
    assert result["error"] is not None
    assert "timeout" in result["error"].lower() or "timed" in result["error"].lower()
    assert result["responseText"] is None


@pytest.mark.asyncio
async def test_run_prompt_http_error_returns_error_field():
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.HTTPError("connection refused"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("backend.routers.run_prompt.os.getenv", return_value="test-key"),
        patch("backend.routers.run_prompt.httpx.AsyncClient", return_value=mock_client),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
            response = await ac.post("/api/run-prompt", json={"prompt": "test", "selected_llms": ["CLAUDE"]})

    assert response.status_code == status.HTTP_200_OK
    result = response.json()["results"][0]
    assert result["error"] == "connection refused"
    assert result["responseText"] is None


@pytest.mark.asyncio
async def test_run_prompt_multiple_llms_returns_all_results():
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"content": [{"text": "ok"}]}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("backend.routers.run_prompt.os.getenv", return_value="test-key"),
        patch("backend.routers.run_prompt.httpx.AsyncClient", return_value=mock_client),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
            response = await ac.post(
                "/api/run-prompt",
                json={"prompt": "test", "selected_llms": ["CLAUDE", "OPENAI", "COHERE"]},
            )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 3


@pytest.mark.asyncio
async def test_run_prompt_concurrent_calls_limited_to_3():
    """Semaphore must prevent more than 3 simultaneous in-flight LLM calls."""
    active = [0]
    max_concurrent = [0]

    async def fake_post(*args, **kwargs):
        active[0] += 1
        max_concurrent[0] = max(max_concurrent[0], active[0])
        await asyncio.sleep(0.05)
        active[0] -= 1
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json.return_value = {"content": [{"text": "ok"}]}
        return resp

    mock_client = AsyncMock()
    mock_client.post = fake_post
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("backend.routers.run_prompt.os.getenv", return_value="test-key"),
        patch("backend.routers.run_prompt.httpx.AsyncClient", return_value=mock_client),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
            response = await ac.post(
                "/api/run-prompt",
                json={
                    "prompt": "test",
                    "selected_llms": ["CLAUDE", "OPENAI", "COHERE", "CLAUDE", "OPENAI"],
                },
            )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 5
    assert max_concurrent[0] <= 3


@pytest.mark.asyncio
async def test_run_prompt_latency_is_non_negative_int():
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"content": [{"text": "response"}]}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("backend.routers.run_prompt.os.getenv", return_value="test-key"),
        patch("backend.routers.run_prompt.httpx.AsyncClient", return_value=mock_client),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
            response = await ac.post("/api/run-prompt", json={"prompt": "test", "selected_llms": ["CLAUDE"]})

    result = response.json()["results"][0]
    assert isinstance(result["latencyMs"], int)
    assert result["latencyMs"] >= 0
