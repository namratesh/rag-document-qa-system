"""Retrieval-only endpoint: vector-searches ingested document chunks.
Useful for debugging retrieval independent of the chat endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from ...config.logger import get_logger
from ...ingest.embed import Embedder
from ...store import vector_store
from ..schemas import QueryRequest, QueryResponse, RetrievedChunk

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query", response_model=QueryResponse)
def query(payload: QueryRequest) -> QueryResponse:
    logger.info("[query] input query=%r top_k=%d", payload.query, payload.top_k)
    embedding = Embedder().embed_query(payload.query)
    results = [RetrievedChunk(**c) for c in vector_store.query(embedding, top_k=payload.top_k)]
    logger.info("[query] output results=%d", len(results))
    return QueryResponse(query=payload.query, results=results)
