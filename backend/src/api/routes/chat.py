"""Conversational Q&A endpoint: retrieves relevant chunks, asks the LLM to
answer with citations, and persists each turn per conversation.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from ...config.logger import get_logger
from ...config.settings import settings
from ...rag.answer import generate_answer, stream_answer
from ...store import history_store
from ..schemas import Citation, MessageRequest, MessageResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/api/conversations", tags=["chat"])


def _to_citations(chunks: list[dict]) -> list[Citation]:
    return [Citation(**c) for c in chunks]


@router.post("/{conv_id}/messages", response_model=MessageResponse)
def send_message(conv_id: str, payload: MessageRequest) -> MessageResponse:
    if history_store.get_full_thread(conv_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    history = history_store.load_recent_turns(conv_id, limit=settings.history_max_turns)
    logger.info(
        "[send_message] input conv_id=%s history_turns=%d message=%r",
        conv_id,
        len(history),
        payload.message,
    )

    answer, chunks = generate_answer(payload.message, history=history)
    citations = _to_citations(chunks)

    history_store.append_turn(conv_id, "user", payload.message)
    history_store.append_turn(conv_id, "assistant", answer, citations=chunks)

    logger.info("[send_message] output answer_len=%d citations=%d", len(answer), len(citations))
    return MessageResponse(conv_id=conv_id, answer=answer, citations=citations)


@router.post("/{conv_id}/messages/stream")
def send_message_stream(conv_id: str, payload: MessageRequest) -> StreamingResponse:
    """Server-Sent Events variant of `send_message`: streams the answer as
    `delta` events, then a `done` event with the final answer/citations."""
    if history_store.get_full_thread(conv_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    history = history_store.load_recent_turns(conv_id, limit=settings.history_max_turns)
    logger.info(
        "[send_message_stream] input conv_id=%s history_turns=%d message=%r",
        conv_id,
        len(history),
        payload.message,
    )

    def event_stream():
        final_answer = ""
        citations: list[dict] = []
        for event in stream_answer(payload.message, history=history):
            if event["type"] == "done":
                final_answer = event["answer"]
                citations = event["citations"]
            yield f"data: {json.dumps(event)}\n\n"

        history_store.append_turn(conv_id, "user", payload.message)
        history_store.append_turn(conv_id, "assistant", final_answer, citations=citations)
        logger.info(
            "[send_message_stream] output answer_len=%d citations=%d",
            len(final_answer),
            len(citations),
        )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
