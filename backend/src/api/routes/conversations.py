"""Conversation lifecycle endpoints: list, create, and fetch a full thread."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from ...config.logger import get_logger
from ...store import history_store
from ..schemas import ConversationSummary, ConversationThreadResponse, CreateConversationResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationSummary])
def list_conversations() -> list[ConversationSummary]:
    conversations = history_store.list_conversations()
    return [ConversationSummary(**c) for c in conversations]


@router.post("", response_model=CreateConversationResponse)
def create_conversation() -> CreateConversationResponse:
    conv_id = str(uuid4())
    history_store.create_conversation(conv_id)
    logger.info("Created conversation %s", conv_id)
    return CreateConversationResponse(conv_id=conv_id)


@router.get("/{conv_id}", response_model=ConversationThreadResponse)
def get_conversation(conv_id: str) -> ConversationThreadResponse:
    thread = history_store.get_full_thread(conv_id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return ConversationThreadResponse(conv_id=conv_id, messages=thread)
