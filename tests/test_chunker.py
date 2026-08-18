from src.ingest.chunker import chunk_document
from src.ingest.parser import ParsedDocument, ParsedPage


def test_chunk_document_tracks_page_numbers():
    parsed = ParsedDocument(
        filename="Annual Report.pdf",
        pages=[
            ParsedPage(page_number=1, text="Revenue grew 12% year over year."),
            ParsedPage(page_number=2, text="Net profit margin improved to 18%."),
        ],
    )

    chunks = chunk_document(parsed)

    assert [c["page_number"] for c in chunks] == [1, 2]
    assert all(c["doc_id"] == "annual-report" for c in chunks)
    assert all(c["filename"] == "Annual Report.pdf" for c in chunks)
    assert chunks[0]["text"] == "Revenue grew 12% year over year."


def test_chunk_document_skips_blank_pages():
    parsed = ParsedDocument(
        filename="doc.pdf",
        pages=[ParsedPage(page_number=1, text=""), ParsedPage(page_number=2, text="Hello world.")],
    )

    chunks = chunk_document(parsed)

    assert len(chunks) == 1
    assert chunks[0]["page_number"] == 2


def test_chunk_document_splits_long_pages_with_overlap():
    long_text = " ".join(f"word{i}" for i in range(400))
    parsed = ParsedDocument(filename="long.pdf", pages=[ParsedPage(page_number=1, text=long_text)])

    chunks = chunk_document(parsed)

    assert len(chunks) > 1
    assert all(len(c["text"]) <= 1000 for c in chunks)
    # chunk_ids are unique and stable
    assert len({c["chunk_id"] for c in chunks}) == len(chunks)
