from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CASE_PILOT_", env_file=".env", extra="ignore")

    anthropic_api_key: str | None = None
    model: str = "claude-sonnet-4-6"

    corpus_dir: Path = Path("data/corpus")
    traces_dir: Path = Path("traces")
    top_k: int = 6

    use_mock_llm: bool = False
    max_agent_steps: int = 6


def get_settings() -> Settings:
    s = Settings()
    if s.anthropic_api_key is None:
        s.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    return s
