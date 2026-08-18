"""Conversation history storage, backed by a local SQLite file."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src.config.settings import settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    conv_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conv_id TEXT NOT NULL REFERENCES conversations(conv_id),
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    citations TEXT,
    created_at TEXT NOT NULL
);
"""


def _connect() -> sqlite3.Connection:
    db_path = Path(settings.sqlite_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_conversation(conv_id: str) -> None:
    now = _now()
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO conversations (conv_id, created_at, updated_at) VALUES (?, ?, ?)",
            (conv_id, now, now),
        )


def list_conversations() -> list[dict]:
    with _connect() as conn:
        conversations = conn.execute(
            "SELECT conv_id, updated_at FROM conversations ORDER BY updated_at DESC"
        ).fetchall()
        result = []
        for conv in conversations:
            first_message = conn.execute(
                "SELECT content FROM messages WHERE conv_id = ? AND role = 'user' "
                "ORDER BY id ASC LIMIT 1",
                (conv["conv_id"],),
            ).fetchone()
            content = first_message["content"] if first_message else ""
            title = content[:60] + "…" if len(content) > 60 else content
            result.append(
                {
                    "conv_id": conv["conv_id"],
                    "title": title or "New conversation",
                    "updated_at": conv["updated_at"],
                }
            )
        return result


def get_full_thread(conv_id: str) -> list[dict] | None:
    with _connect() as conn:
        conv = conn.execute(
            "SELECT conv_id FROM conversations WHERE conv_id = ?", (conv_id,)
        ).fetchone()
        if not conv:
            return None
        rows = conn.execute(
            "SELECT role, content, citations FROM messages WHERE conv_id = ? ORDER BY id ASC",
            (conv_id,),
        ).fetchall()
        return [
            {
                "role": r["role"],
                "content": r["content"],
                "citations": json.loads(r["citations"]) if r["citations"] else [],
            }
            for r in rows
        ]


def load_recent_turns(conv_id: str, limit: int) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE conv_id = ? ORDER BY id DESC LIMIT ?",
            (conv_id, limit),
        ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def append_turn(
    conv_id: str,
    role: str,
    content: str,
    citations: list[dict] | None = None,
) -> None:
    now = _now()
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO conversations (conv_id, created_at, updated_at) VALUES (?, ?, ?)",
            (conv_id, now, now),
        )
        conn.execute(
            "INSERT INTO messages (conv_id, role, content, citations, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (conv_id, role, content, json.dumps(citations) if citations else None, now),
        )
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE conv_id = ?", (now, conv_id)
        )
