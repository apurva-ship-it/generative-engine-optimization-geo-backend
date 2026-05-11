from fastapi import APIRouter, HTTPException, status
import httpx
import os
from typing import List
from ..schemas.generate_prompts import GeneratePromptRequest, GeneratePromptResponse, PromptItem

router = APIRouter(prefix="/api", tags=["generate-prompts"])

# Helper to build a prompt item (could be replaced with real LLM output)
def build_prompt_item(idx: int, topic: str) -> PromptItem:
    return PromptItem(
        title=f"Prompt {idx+1} for {topic}",
        strategyTag=f"strategy-{idx+1}",
        description=f"Description of strategy {idx+1} for topic {topic}",
        prompt=f"Generate content about {topic} using strategy {idx+1}"
    )

@router.post("/generate-prompts", response_model=GeneratePromptResponse, status_code=status.HTTP_200_OK)
async def generate_prompts(request: GeneratePromptRequest) -> GeneratePromptResponse:
    """Generate eight prompts for a given topic using Claude.

    The endpoint validates the request payload via Pydantic. It then calls the
    external Claude API (or falls back to a stub when the API key is missing).
    The response always contains exactly eight prompt objects.
    """
    api_key = os.getenv("CLAUDE_API_KEY")
    # If API key is configured, attempt real call; otherwise use stub data.
    if api_key:
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.post(
                    "https://api.anthropic.com/v1/complete",
                    json={
                        "model": "claude-2.1",
                        "prompt": f"Generate eight distinct prompts for the topic: {request.topic}. Return JSON with fields title, strategyTag, description, prompt.",
                        "max_tokens": 1024,
                    },
                    headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
                )
                resp.raise_for_status()
                data = resp.json()
                # Assume the LLM returns a JSON list under 'completion'
                prompts_raw: List[dict] = data.get("completion", [])
                prompts: List[PromptItem] = []
                for item in prompts_raw:
                    try:
                        prompts.append(PromptItem(**item))
                    except Exception:
                        # skip malformed items
                        continue
                # Ensure exactly eight prompts; fill missing with stubs
                if len(prompts) < 8:
                    for i in range(len(prompts), 8):
                        prompts.append(build_prompt_item(i, request.topic))
                elif len(prompts) > 8:
                    prompts = prompts[:8]
                return GeneratePromptResponse(prompts=prompts)
            except httpx.HTTPError as e:
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    # Fallback stub generation
    prompts = [build_prompt_item(i, request.topic) for i in range(8)]
    return GeneratePromptResponse(prompts=prompts)
