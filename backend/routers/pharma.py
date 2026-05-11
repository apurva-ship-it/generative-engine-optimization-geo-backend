from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..dependencies import get_db
from ..schemas.pharma import PharmaPrompt, PharmaResponse
import httpx
import os

router = APIRouter(prefix="/api/v1/pharma", tags=["pharma"])

@router.post("/prompt", response_model=PharmaResponse, status_code=status.HTTP_200_OK)
async def create_pharma_prompt(prompt: PharmaPrompt, db: AsyncSession = Depends(get_db)):
    """Accept a prompt, call external LLM service and return response.
    Validation is enforced by Pydantic schema PharmaPrompt.
    """
    # Example external call (placeholder)
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="LLM API key not configured")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                "https://api.example.com/llm",
                json={"prompt": prompt.text},
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30,
            )
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    data = resp.json()
    return PharmaResponse(result=data.get("result", ""))
