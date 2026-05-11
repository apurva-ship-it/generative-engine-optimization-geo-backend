from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List

class RunPromptRequest(BaseModel):
    prompt: str
    selected_llms: List[str]

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class RunPromptResult(BaseModel):
    llm_name: str = Field(alias="llmName")
    response_text: Optional[str] = Field(default=None, alias="responseText")
    latency_ms: int = Field(alias="latencyMs")
    error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class RunPromptResponse(BaseModel):
    results: List[RunPromptResult]

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
