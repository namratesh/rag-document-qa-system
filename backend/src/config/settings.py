"""Centralized application settings, loaded from environment / .env."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root .env, resolved from this file's location so it loads regardless of cwd.
_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, env_prefix="", extra="ignore")

    app_name: str = "doc-qa"
    env: str = "development"

    # Logging
    log_level: str = "INFO"
    log_dir: str = "logs"
    log_to_file: bool = True

    # OpenRouter (OpenAI-compatible API) - used for both embeddings and chat completions.
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    embedding_model_name: str = "nvidia/nemotron-3-embed-1b:free"
    embedding_batch_size: int = 32
    chat_model_name: str = "openai/gpt-4o-mini"
    chat_temperature: float = 0.1
    chat_max_tokens: int = 800
    chat_top_k: int = 5

    # Storage (local, file-based - no external services required)
    chroma_dir: str = "storage/chroma"
    sqlite_path: str = "storage/history.db"
    history_max_turns: int = 6


settings = Settings()
