from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Dxora AI Link Analysis API"
    llm_provider: str = "gemini"
    llm_model: str = "gemini-3.1-flash-lite-preview"
    gemini_api_key: Optional[str] = Field(default=None, repr=False)
    request_timeout_seconds: float = 15.0
    max_download_bytes: int = 2_000_000
    max_content_chars: int = 24_000


@lru_cache
def get_settings() -> Settings:
    return Settings()
