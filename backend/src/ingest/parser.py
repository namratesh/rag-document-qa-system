"""Extract per-page text from a PDF using pypdf."""

from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO

from pypdf import PdfReader

from src.config.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ParsedPage:
    page_number: int
    text: str


@dataclass
class ParsedDocument:
    filename: str
    pages: list[ParsedPage]


def parse_pdf(file: BinaryIO, filename: str) -> ParsedDocument:
    logger.info("[parse_pdf] input filename=%s", filename)
    reader = PdfReader(file)
    pages = [
        ParsedPage(page_number=i, text=page.extract_text() or "")
        for i, page in enumerate(reader.pages, start=1)
    ]
    logger.info("[parse_pdf] output filename=%s pages=%d", filename, len(pages))
    return ParsedDocument(filename=filename, pages=pages)
