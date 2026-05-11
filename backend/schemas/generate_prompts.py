from pydantic import BaseModel, Field, ConfigDict
from typing import List

class GeneratePromptRequest(BaseModel):
    """Request body for generating prompts.

    The `topic` field describes the subject for which prompts should be generated.
    """

    topic: str = Field(..., min_length=1, description="Topic for which to generate prompts")

    model_config = ConfigDict(from_attributes=True)

class PromptItem(BaseModel):
    title: str
    strategyTag: str
    description: str
    prompt: str

    model_config = ConfigDict(from_attributes=True)

class GeneratePromptResponse(BaseModel):
    prompts: List[PromptItem]

    model_config = ConfigDict(from_attributes=True)
