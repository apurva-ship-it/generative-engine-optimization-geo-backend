from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    allowed_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}
