import pytest

from src.config.settings import settings
from src.store import history_store


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "sqlite_path", str(tmp_path / "history.db"))
    yield


def test_new_conversation_has_no_thread_until_created():
    assert history_store.get_full_thread("missing") is None

    history_store.create_conversation("conv-1")

    assert history_store.get_full_thread("conv-1") == []


def test_append_turn_persists_role_content_and_citations():
    history_store.create_conversation("conv-1")
    history_store.append_turn("conv-1", "user", "What was revenue?")
    history_store.append_turn(
        "conv-1",
        "assistant",
        "Revenue grew 12%.",
        citations=[{"filename": "report.pdf", "page_number": 3}],
    )

    thread = history_store.get_full_thread("conv-1")

    assert [t["role"] for t in thread] == ["user", "assistant"]
    assert thread[1]["citations"] == [{"filename": "report.pdf", "page_number": 3}]


def test_load_recent_turns_respects_limit_and_order():
    history_store.create_conversation("conv-1")
    for i in range(5):
        history_store.append_turn("conv-1", "user", f"question {i}")

    recent = history_store.load_recent_turns("conv-1", limit=2)

    assert [t["content"] for t in recent] == ["question 3", "question 4"]


def test_list_conversations_orders_by_most_recently_updated():
    history_store.create_conversation("conv-a")
    history_store.append_turn("conv-a", "user", "first conversation")
    history_store.create_conversation("conv-b")
    history_store.append_turn("conv-b", "user", "second conversation")

    conversations = history_store.list_conversations()

    assert [c["conv_id"] for c in conversations] == ["conv-b", "conv-a"]
    assert conversations[0]["title"] == "second conversation"
