"""Local vector store for document chunks, backed by an on-disk Chroma
collection (no external DB service to run).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import chromadb

from src.config.logger import get_logger
from src.config.settings import settings

logger = get_logger(__name__)

_COLLECTION_NAME = "documents"


@lru_cache(maxsize=1)
def get_collection():
    persist_dir = Path(settings.chroma_dir)
    persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_dir))
    return client.get_or_create_collection(name=_COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def upsert_chunks(chunks: list[dict], embeddings: list[list[float]]) -> None:
    if not chunks:
        return
    collection = get_collection()
    collection.upsert(
        ids=[c["chunk_id"] for c in chunks],
        embeddings=embeddings,
        documents=[c["text"] for c in chunks],
        metadatas=[
            {"doc_id": c["doc_id"], "filename": c["filename"], "page_number": c["page_number"]}
            for c in chunks
        ],
    )
    logger.info("[upsert_chunks] output stored=%d", len(chunks))


def query(embedding: list[float], top_k: int = 5) -> list[dict]:
    collection = get_collection()
    count = collection.count()
    if count == 0:
        return []

    result = collection.query(query_embeddings=[embedding], n_results=min(top_k, count))
    results: list[dict] = []
    for chunk_id, text, meta, distance in zip(
        result["ids"][0], result["documents"][0], result["metadatas"][0], result["distances"][0]
    ):
        results.append(
            {
                "chunk_id": chunk_id,
                "text": text,
                "doc_id": meta["doc_id"],
                "filename": meta["filename"],
                "page_number": meta["page_number"],
                "score": 1 - distance,
            }
        )
    return results


def list_documents() -> list[dict]:
    collection = get_collection()
    if collection.count() == 0:
        return []

    data = collection.get(include=["metadatas"])
    documents: dict[str, dict] = {}
    for meta in data["metadatas"]:
        doc = documents.setdefault(
            meta["doc_id"], {"doc_id": meta["doc_id"], "filename": meta["filename"], "chunk_count": 0}
        )
        doc["chunk_count"] += 1
    return list(documents.values())
