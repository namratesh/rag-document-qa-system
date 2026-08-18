"""Split a parsed PDF's per-page text into overlapping chunks for embedding.

Each chunk keeps the page number it came from so answers can cite exactly
where in the document a piece of text was found.
"""

from __future__ import annotations

import re
from pathlib import Path

from src.config.logger import get_logger
from src.ingest.parser import ParsedDocument

logger = get_logger(__name__)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def _slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    return slug or "document"


def _split_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    if len(text) <= size:
        return [text]

    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            # Avoid cutting mid-word: back off to the last whitespace in range.
            boundary = text.rfind(" ", start, end)
            if boundary > start:
                end = boundary
        pieces.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return [p for p in pieces if p]


def chunk_document(parsed: ParsedDocument) -> list[dict]:
    logger.info("[chunk_document] input filename=%s pages=%d", parsed.filename, len(parsed.pages))
    doc_id = _slugify(Path(parsed.filename).stem)

    chunks: list[dict] = []
    idx = 0
    for page in parsed.pages:
        text = re.sub(r"\s+", " ", page.text).strip()
        if not text:
            continue
        for piece in _split_text(text):
            idx += 1
            chunks.append(
                {
                    "chunk_id": f"{doc_id}_p{page.page_number:03d}_{idx:04d}",
                    "doc_id": doc_id,
                    "filename": parsed.filename,
                    "page_number": page.page_number,
                    "text": piece,
                }
            )

    logger.info("[chunk_document] output doc_id=%s chunks=%d", doc_id, len(chunks))
    return chunks
