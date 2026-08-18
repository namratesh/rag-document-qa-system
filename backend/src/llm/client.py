"""Chat-completion client, via the OpenAI SDK pointed at OpenRouter (an
OpenAI-compatible API)."""

from __future__ import annotations

from functools import lru_cache
from typing import Iterator

from openai import OpenAI

from src.config.logger import get_logger
from src.config.settings import settings

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    if not settings.openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY is not set. Add it to .env to use chat completions.")
    return OpenAI(api_key=settings.openrouter_api_key, base_url=settings.openrouter_base_url)


def chat_completion(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.0,
    model: str | None = None,
) -> str:
    client = get_openai_client()
    model_name = model or settings.chat_model_name
    logger.info("[chat_completion] input model=%s messages=%d", model_name, len(messages))
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=settings.chat_max_tokens,
    )
    content = response.choices[0].message.content or ""
    logger.info("[chat_completion] output content_len=%d", len(content))
    return content


def stream_chat_completion(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.0,
    model: str | None = None,
) -> Iterator[str]:
    client = get_openai_client()
    model_name = model or settings.chat_model_name
    logger.info("[stream_chat_completion] input model=%s messages=%d", model_name, len(messages))
    stream = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=settings.chat_max_tokens,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
