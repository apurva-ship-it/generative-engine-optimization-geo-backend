from pydantic import BaseModel, Field
from pydantic import ConfigDict

class PharmaPrompt(BaseModel):
    text: str = Field(..., min_length=1, description="Prompt text for the LLM")
    model_config = ConfigDict(from_attributes=True)

class PharmaResponse(BaseModel):
    result: str
    model_config = ConfigDict(from_attributes=True)
