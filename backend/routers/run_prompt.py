from fastapi import APIRouter, HTTPException, status
from typing import List
import os
import httpx
import asyncio
from ..schemas.run_prompt import RunPromptRequest, RunPromptResponse, RunPromptResult

router = APIRouter(prefix="/api", tags=["run-prompt"])

# simple mapping from llm name to endpoint URL (could be expanded)
LLM_ENDPOINTS = {
    "CLAUDE": "https://api.anthropic.com/v1/complete",
    "OPENAI": "https://api.openai.com/v1/completions",
    "COHERE": "https://api.cohere.com/v1/generate",
}

async def call_llm(llm_name: str, prompt: str, client: httpx.AsyncClient) -> RunPromptResult:
    start = asyncio.get_event_loop().time()
    endpoint = LLM_ENDPOINTS.get(llm_name.upper())
    api_key = os.getenv(f"{llm_name.upper()}_API_KEY")
    if not endpoint or not api_key:
        latency_ms = int((asyncio.get_event_loop().time() - start) * 1000)
        return RunPromptResult(
            llm_name=llm_name,
            response_text=None,
            latency_ms=latency_ms,
            error="LLM configuration missing",
        )
    try:
        resp = await client.post(
            endpoint,
            json={"prompt": prompt},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        # naive extraction – varies per provider, use 'text' fallback
        text = data.get("text") or data.get("choices", [{}])[0].get("text") or ""
        latency_ms = int((asyncio.get_event_loop().time() - start) * 1000)
        return RunPromptResult(
            llm_name=llm_name,
            response_text=text,
            latency_ms=latency_ms,
            error=None,
        )
    except httpx.HTTPError as e:
        latency_ms = int((asyncio.get_event_loop().time() - start) * 1000)
        return RunPromptResult(
            llm_name=llm_name,
            response_text=None,
            latency_ms=latency_ms,
            error=str(e),
        )

@router.post("/run-prompt", response_model=RunPromptResponse, status_code=status.HTTP_200_OK)
async def run_prompt(request: RunPromptRequest) -> RunPromptResponse:
    """Invoke selected LLMs concurrently (max 3) with a 30 s timeout per call.

    Returns an array with each LLM's name, response text, latency, and optional error.
    """
    if not request.selected_llms:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No LLM selected")

    semaphore = asyncio.Semaphore(3)
    results: List[RunPromptResult] = []
    async with httpx.AsyncClient() as client:
        async def limited_call(llm: str) -> None:
            async with semaphore:
                res = await call_llm(llm, request.prompt, client)
                results.append(res)
        # schedule all calls
        await asyncio.gather(*[limited_call(llm) for llm in request.selected_llms])
    return RunPromptResponse(results=results)
