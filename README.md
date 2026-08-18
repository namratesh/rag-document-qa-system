# Document Q&A

A small RAG (retrieval-augmented generation) app: upload up to three PDFs, ask
natural-language questions about them, and get an answer with citations back
to the document and page it came from.

## Table of contents

- [Features](#features)
- [Tech stack](#tech-stack)
- [Architecture](#architecture)
- [Getting started](#getting-started)
- [Using the API directly](#using-the-api-directly)
- [Testing](#testing)
- [Known limitations](#known-limitations)
- [Improvements with more time](#improvements-with-more-time)

## Features

- Upload 1-3 PDFs through the UI (or the API directly) — the running app
  parses, chunks, embeds, and stores them itself; no offline ingestion step.
- Ask questions in a chat UI; answers cite the source **document filename
  and page number**, with the retrieved excerpt shown on demand.
- Multi-turn conversation history, so follow-up questions ("what about last
  quarter?") reuse prior turns as context.
- Streaming (SSE) answers, plus a plain JSON endpoint for the same thing.
- Runs with a single command: `docker compose up --build`.

## Tech stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI, Pydantic v2 |
| PDF parsing | [`pypdf`](https://pypi.org/project/pypdf/) (per-page text extraction) |
| Chunking | simple recursive character splitter, page number preserved per chunk |
| Embeddings + chat completions | [OpenRouter](https://openrouter.ai) (OpenAI-compatible HTTP API) |
| Vector store | [Chroma](https://www.trychroma.com/), persisted to a local file |
| Conversation history | SQLite, persisted to a local file |
| Frontend | React + TypeScript (Vite), served via nginx |
| Orchestration | Docker Compose |

Both the vector store and the conversation history are plain local files, so
`docker compose up` is the entire setup — no second container to wait on and
no connection string to configure.

## Architecture

```
PDF upload (UI or curl)
  -> ingest/parser.py     pypdf: extract text per page
  -> ingest/chunker.py    split each page into ~1000-char chunks (page number kept)
  -> ingest/embed.py      embed each chunk via OpenRouter
  -> store/vector_store.py   upsert into a local Chroma collection

Question (chat UI or curl)
  -> ingest/embed.py      embed the question
  -> store/vector_store.py   cosine-similarity search, top-k chunks
  -> rag/answer.py        build a prompt: system instructions + chunks + question
  -> llm/client.py        chat completion (streamed or not) via OpenRouter
  -> store/history_store.py  persist the turn (SQLite), keyed by conv_id
  -> answer + citations back to the UI
```

There's no multi-agent framework in the loop — retrieval and generation are
two plain function calls (`rag/answer.py`), which is all a single-turn RAG
Q&A app needs. The LLM is instructed to cite `(filename, p. N)` inline as
part of the answer, and the API separately returns the top-k retrieved
chunks as structured citations so the UI can show excerpts without
re-parsing the answer text.

Backend layout:

```
backend/src/
  api/            FastAPI app, routes, Pydantic schemas
  ingest/         PDF parsing, chunking, embedding
  store/          Chroma vector store, SQLite conversation history
  llm/            OpenRouter chat-completion client
  rag/            retrieval + prompt building + answer generation
  config/         settings (.env) and logging
```

## Getting started

Requires Docker and Docker Compose.

1. Copy `.env.example` to `.env` and add an OpenRouter API key (free to
   create at [openrouter.ai/keys](https://openrouter.ai/keys)):

   ```bash
   cp .env.example .env
   # edit .env, set OPENROUTER_API_KEY=...
   ```

2. Start the app:

   ```bash
   docker compose up --build
   ```

3. Open the UI at **http://localhost:5173**. Upload 1-3 PDFs (sample
   earnings-call transcripts are included in `data/` if you want something
   to try immediately), then ask questions in the chat panel.

The backend API is at `http://localhost:8000` (interactive docs at
`/docs`). Uploaded documents and conversation history persist across
restarts in the `./storage` directory (bind-mounted into the backend
container).

### Running without Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add OPENROUTER_API_KEY

PYTHONPATH=backend uvicorn backend.src.api.main:app --reload
```

Then, separately, run the frontend:

```bash
cd frontend
npm install
npm run dev  # http://localhost:5173, proxies to the backend on :8000
```

## Using the API directly

```bash
# Upload up to 3 PDFs
curl -X POST http://localhost:8000/api/documents \
  -F "files=@data/infosys.pdf"

# Start a conversation and ask a question
CONV=$(curl -s -X POST http://localhost:8000/api/conversations | python3 -c "import sys,json;print(json.load(sys.stdin)['conv_id'])")
curl -X POST http://localhost:8000/api/conversations/$CONV/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "What was revenue growth?"}'
```

`POST /api/query` retrieves chunks directly (no LLM call) — useful for
debugging retrieval quality independent of the chat endpoint.

## Testing

```bash
source .venv/bin/activate
PYTHONPATH=backend python -m pytest tests/
```

Tests cover the chunker (page tracking, blank-page skipping, long-page
splitting) and the SQLite history store (conversation/turn persistence,
recent-turns limit, ordering). They don't hit OpenRouter — no API key
needed to run them. There's no automated test for the retrieval/LLM path
itself; that was verified manually end-to-end (see Known limitations).

## Known limitations

- **No automated retrieval/answer-quality tests.** The RAG pipeline
  (embed -> retrieve -> generate) was verified manually against the sample
  PDFs, not via an automated eval set. With more time I'd add a small
  fixture set of question/expected-citation pairs.
- **Chunking is generic, not layout-aware.** It splits page text at a fixed
  character count with a small overlap; it doesn't try to detect headings,
  tables, or paragraph boundaries. Works fine for prose-heavy PDFs (like the
  sample earnings-call transcripts); tables or multi-column layouts will
  chunk less cleanly since `pypdf`'s text extraction doesn't preserve
  layout.
- **No re-ranking.** Retrieval is plain cosine similarity over the top-k
  chunks; there's no cross-encoder re-ranking step, so borderline-relevant
  chunks can occasionally outrank a better one.
- **No document deletion/replacement UI.** Re-uploading a PDF with the same
  filename overwrites its old chunks (upsert by chunk ID), but there's no
  way to remove a document from the corpus without restarting with a fresh
  `./storage` volume.
- **One shared workspace.** All uploaded documents and conversations live in
  one corpus — there's no separation between different sets of documents or
  conversations within a running instance.
- **SQLite/Chroma over a network filesystem.** The `./storage` bind mount
  assumes a local disk; SQLite in particular doesn't behave well over NFS.
  Not an issue for local/single-instance use.

## Improvements with more time

- A small evaluation set (sample questions + expected source page) run in
  CI to catch retrieval/prompt regressions.
- Layout-aware chunking (e.g. detect headings/tables) for cleaner citations
  on structured documents.
- A re-ranking step (cross-encoder or LLM-based) over the top-k candidates
  before building the answer prompt.
- Per-conversation document scoping, so a question only retrieves from the
  documents relevant to that conversation instead of the whole shared
  corpus.
- Document management (list with delete/replace) in the UI, instead of only
  upload.
