"""Document upload endpoint: accepts up to 3 PDFs and runs them through
parse -> chunk -> embed -> store, so the running app itself is what makes
documents queryable (no separate offline ingestion step).
"""

from __future__ import annotations

import io

from fastapi import APIRouter, HTTPException, UploadFile, status

from ...config.logger import get_logger
from ...ingest.chunker import chunk_document
from ...ingest.embed import Embedder
from ...ingest.parser import parse_pdf
from ...store import vector_store
from ..schemas import DocumentsResponse, DocumentSummary, UploadDocumentsResponse, UploadedDocument

logger = get_logger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

MAX_FILES_PER_UPLOAD = 3


@router.post("", response_model=UploadDocumentsResponse)
async def upload_documents(files: list[UploadFile]) -> UploadDocumentsResponse:
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided")
    if len(files) > MAX_FILES_PER_UPLOAD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Upload at most {MAX_FILES_PER_UPLOAD} PDFs at a time",
        )
    for f in files:
        if not (f.filename or "").lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{f.filename!r} is not a PDF",
            )

    embedder = Embedder()
    uploaded: list[UploadedDocument] = []
    for f in files:
        logger.info("[upload_documents] step: parsing %s", f.filename)
        body = await f.read()
        parsed = parse_pdf(io.BytesIO(body), filename=f.filename or "document.pdf")

        chunks = chunk_document(parsed)
        if not chunks:
            logger.warning("[upload_documents] %s produced no extractable text; skipping", f.filename)
            continue

        embeddings = embedder.embed_documents([c["text"] for c in chunks])
        vector_store.upsert_chunks(chunks, embeddings)

        uploaded.append(
            UploadedDocument(
                filename=parsed.filename,
                doc_id=chunks[0]["doc_id"],
                pages=len(parsed.pages),
                chunks_stored=len(chunks),
            )
        )
        logger.info(
            "[upload_documents] output %s -> doc_id=%s chunks=%d",
            f.filename,
            chunks[0]["doc_id"],
            len(chunks),
        )

    return UploadDocumentsResponse(documents=uploaded)


@router.get("", response_model=DocumentsResponse)
def list_documents() -> DocumentsResponse:
    documents = [DocumentSummary(**d) for d in vector_store.list_documents()]
    return DocumentsResponse(documents=documents)
