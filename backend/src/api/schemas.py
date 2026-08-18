"""Pydantic request/response models for the API layer."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


class RetrievedChunk(BaseModel):
    chunk_id: str
    doc_id: str
    filename: str
    page_number: int
    text: str
    score: float


class QueryResponse(BaseModel):
    query: str
    results: list[RetrievedChunk]


class MessageRequest(BaseModel):
    message: str


class Citation(BaseModel):
    chunk_id: str
    doc_id: str
    filename: str
    page_number: int
    text: str
    score: float


class MessageResponse(BaseModel):
    conv_id: str
    answer: str
    citations: list[Citation] = []


class ConversationSummary(BaseModel):
    conv_id: str
    title: str
    updated_at: str


class CreateConversationResponse(BaseModel):
    conv_id: str


class ThreadMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    citations: list[Citation] = []


class ConversationThreadResponse(BaseModel):
    conv_id: str
    messages: list[ThreadMessage]


class UploadedDocument(BaseModel):
    filename: str
    doc_id: str
    pages: int
    chunks_stored: int


class UploadDocumentsResponse(BaseModel):
    documents: list[UploadedDocument]


class DocumentSummary(BaseModel):
    doc_id: str
    filename: str
    chunk_count: int


class DocumentsResponse(BaseModel):
    documents: list[DocumentSummary]
