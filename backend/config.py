from typing import List

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    Environment variables:
        - ALLOWED_ORIGINS: Comma‑separated list of origins allowed for CORS.
        - Other settings may be added in the future.
    """

    allowed_origins: List[str] = Field(default_factory=list, env="ALLOWED_ORIGINS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
