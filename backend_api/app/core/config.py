from functools import lru_cache
from pathlib import Path
import sys

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_API_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or a .env file."""

    database_url: str
    python_bin_path: str = sys.executable
    trino_mcp_dir: str | None = None
    gemini_api_key: str | None = None
    llm_timeout_seconds: float = 20.0
    available_models: list[str] = [
        "models/gemini-2.5-flash",
        "models/gemini-3.5-flash",
        "models/gemini-3.1-flash-lite",
        "models/gemini-3.5-flash-lite",
        "models/gemini-3.6-flash",
        "models/gemini-3.5-flash",
        "models/gemini-2.5-flash",
        "models/gemma-4-26b-a4b-it"
    ]

    model_config = SettingsConfigDict(
        env_file=BACKEND_API_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
