"""Retrieval-augmented answer generation: embed the question, fetch the
top-k most relevant chunks, and ask the LLM to answer using only those
excerpts, citing the source document and page inline.

Returns citations as plain dicts (matching `vector_store.query`'s shape)
rather than the `Citation` pydantic model -- that model lives in
`api/schemas.py` and gets constructed at the API route layer, so this
module stays independent of the API's import path.
"""

from __future__ import annotations

from typing import Iterator

from src.config.logger import get_logger
from src.config.settings import settings
from src.ingest.embed import Embedder
from src.llm.client import chat_completion, stream_chat_completion
from src.store import vector_store

logger = get_logger(__name__)

SYSTEM_PROMPT = (
    "You are a helpful assistant answering questions about a small set of uploaded PDF "
    "documents. Answer strictly using the excerpts provided below the question; do not "
    "use outside knowledge. If the excerpts don't contain the answer, say you don't know "
    "instead of guessing. Whenever you use information from an excerpt, cite it inline "
    "right after the relevant sentence as (filename, p. N). Keep answers concise."
)


def _format_context(chunks: list[dict]) -> str:
    return "\n\n".join(
        f"Source: {c['filename']}, page {c['page_number']}\n{c['text']}" for c in chunks
    )


def _retrieve(question: str, top_k: int) -> list[dict]:
    embedder = Embedder()
    query_embedding = embedder.embed_query(question)
    return vector_store.query(query_embedding, top_k=top_k)


def _build_messages(question: str, chunks: list[dict], history: list[dict]) -> list[dict[str, str]]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend({"role": t["role"], "content": t["content"]} for t in history)
    context = _format_context(chunks) if chunks else "(no relevant excerpts found)"
    messages.append({"role": "user", "content": f"Excerpts:\n{context}\n\nQuestion: {question}"})
    return messages


def generate_answer(
    question: str, history: list[dict] | None = None, top_k: int | None = None
) -> tuple[str, list[dict]]:
    top_k = top_k or settings.chat_top_k
    logger.info("[generate_answer] input question=%r top_k=%d", question, top_k)
    chunks = _retrieve(question, top_k)
    messages = _build_messages(question, chunks, history or [])
    answer = chat_completion(messages, temperature=settings.chat_temperature)
    logger.info("[generate_answer] output answer_len=%d citations=%d", len(answer), len(chunks))
    return answer, chunks


def stream_answer(
    question: str, history: list[dict] | None = None, top_k: int | None = None
) -> Iterator[dict]:
    top_k = top_k or settings.chat_top_k
    logger.info("[stream_answer] input question=%r top_k=%d", question, top_k)
    chunks = _retrieve(question, top_k)
    messages = _build_messages(question, chunks, history or [])

    full_answer: list[str] = []
    for delta in stream_chat_completion(messages, temperature=settings.chat_temperature):
        full_answer.append(delta)
        yield {"type": "delta", "text": delta}

    yield {"type": "done", "answer": "".join(full_answer), "citations": chunks}
