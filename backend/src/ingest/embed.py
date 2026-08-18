"""Embeds text via the OpenRouter embeddings API (HTTP, no local ML model)."""

from __future__ import annotations

import requests

from src.config.logger import get_logger
from src.config.settings import settings

logger = get_logger(__name__)


class Embedder:
    def __init__(self, model_name: str | None = None, api_key: str | None = None) -> None:
        self.model_name = model_name or settings.embedding_model_name
        self.api_key = api_key or settings.openrouter_api_key
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is not set. Add it to .env to use embeddings."
            )
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )
        self._url = f"{settings.openrouter_base_url.rstrip('/')}/embeddings"

    def _request(self, texts: list[str]) -> list[list[float]]:
        response = self._session.post(
            self._url,
            json={"model": self.model_name, "input": texts, "encoding_format": "float"},
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()["data"]
        data.sort(key=lambda item: item["index"])
        return [item["embedding"] for item in data]

    def embed_documents(self, texts: list[str], batch_size: int | None = None) -> list[list[float]]:
        batch_size = batch_size or settings.embedding_batch_size
        embeddings: list[list[float]] = []
        for start in range(0, len(texts), batch_size):
            embeddings.extend(self._request(texts[start : start + batch_size]))
        logger.info("[embed_documents] output embeddings=%d", len(embeddings))
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        return self._request([text])[0]
