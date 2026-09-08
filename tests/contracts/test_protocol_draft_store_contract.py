"""ProtocolDraftStore 契约：InMemory / SQLite 实现同语义（PLAN-20260908-033 AC-03/AC-07）。

覆盖：create/get/list 往返、save 乐观并发、陈旧修订 412 冲突、幂等重放
不产生重复修订、修订不可变性（append-only）、跨 reopen 持久化。
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

import pytest

from adapters.sqlite.protocol_draft_store import SqliteProtocolDraftStore
from packages.application.ports.protocol_draft_store import (
    DraftQuery,
    DraftStoreConflictError,
    ProtocolDraftStore,
)
from packages.application.protocol_authoring.memory_store import InMemoryProtocolDraftStore

_YAML_A = "id: sort_analysis_v1_0_1\nversion: 0.4.0\nphases: []\n"
_YAML_B = _YAML_A + "# edited\n"
_DIGEST_A = "sha256:" + "a" * 64
_DIGEST_B = "sha256:" + "b" * 64


def _clock() -> Callable[[], datetime]:
    counter = {"n": 0}

    def tick() -> datetime:
        counter["n"] += 1
        return datetime(2026, 9, 8, 12, 0, counter["n"], tzinfo=timezone.utc)

    return tick


def _stores() -> tuple[ProtocolDraftStore, ...]:
    return (
        InMemoryProtocolDraftStore(clock=_clock()),
        SqliteProtocolDraftStore(":memory:"),
    )


def test_store_satisfies_port_protocol() -> None:
    for store in _stores():
        assert isinstance(store, ProtocolDraftStore)
        store.close() if hasattr(store, "close") else None


def test_create_get_roundtrip() -> None:
    for store in _stores():
        record = store.create("example-project", "demo", _YAML_A, _DIGEST_A, "key-1")
        assert record.revision == 1
        assert record.name == "demo"
        assert record.source_digest == _DIGEST_A
        fetched = store.get(record.draft_id)
        assert fetched is not None
        assert fetched.yaml_text == _YAML_A
        if hasattr(store, "close"):
            store.close()


def test_create_idempotent_replay_returns_same_record() -> None:
    for store in _stores():
        first = store.create("example-project", "demo", _YAML_A, _DIGEST_A, "key-x")
        second = store.create("example-project", "demo", _YAML_A, _DIGEST_A, "key-x")
        assert first.draft_id == second.draft_id
        assert store.list_revisions(first.draft_id).__len__() == 1
        if hasattr(store, "close"):
            store.close()


def test_save_appends_revision_and_conflicts_on_stale() -> None:
    for store in _stores():
        record = store.create("example-project", "demo", _YAML_A, _DIGEST_A, "key-1")
        draft_id = record.draft_id
        result = store.save(
            draft_id,
            yaml_text=_YAML_B,
            source_digest=_DIGEST_B,
            expected_revision=1,
            idempotency_key="key-2",
        )
        assert result.record.revision == 2
        assert result.replayed is False
        with pytest.raises(DraftStoreConflictError) as excinfo:
            store.save(
                draft_id,
                yaml_text=_YAML_B,
                source_digest=_DIGEST_B,
                expected_revision=1,
                idempotency_key="key-3",
            )
        assert excinfo.value.current_revision == 2
        if hasattr(store, "close"):
            store.close()


def test_save_idempotent_retry_does_not_duplicate_revision() -> None:
    for store in _stores():
        record = store.create("example-project", "demo", _YAML_A, _DIGEST_A, "key-1")
        draft_id = record.draft_id
        first = store.save(
            draft_id,
            yaml_text=_YAML_B,
            source_digest=_DIGEST_B,
            expected_revision=1,
            idempotency_key="retry-key",
        )
        second = store.save(
            draft_id,
            yaml_text=_YAML_B,
            source_digest=_DIGEST_B,
            expected_revision=2,
            idempotency_key="retry-key",
        )
        assert second.replayed is True
        assert second.record.revision == first.record.revision
        assert len(store.list_revisions(draft_id)) == 2
        if hasattr(store, "close"):
            store.close()


def test_revisions_are_immutable_history() -> None:
    for store in _stores():
        record = store.create("example-project", "demo", _YAML_A, _DIGEST_A, "key-1")
        draft_id = record.draft_id
        store.save(
            draft_id,
            yaml_text=_YAML_B,
            source_digest=_DIGEST_B,
            expected_revision=1,
            idempotency_key="key-2",
        )
        revision_one = store.get_revision(draft_id, 1)
        assert revision_one is not None
        assert revision_one.yaml_text == _YAML_A
        current = store.get(draft_id)
        assert current is not None
        assert current.yaml_text == _YAML_B
        assert [r.revision for r in store.list_revisions(draft_id)] == [1, 2]
        if hasattr(store, "close"):
            store.close()


def test_list_orders_by_recency_and_filters_project(tmp_path: Path) -> None:
    store = SqliteProtocolDraftStore(str(tmp_path / "drafts.db"))
    first = store.create("p1", "a", _YAML_A, _DIGEST_A, "k1")
    second = store.create("p1", "b", _YAML_B, _DIGEST_B, "k2")
    store.create("p2", "c", _YAML_A, _DIGEST_A, "k3")
    listed = store.list(DraftQuery(project_id="p1"))
    assert [item.draft_id for item in listed] == [second.draft_id, first.draft_id]
    store.close()

    reopened = SqliteProtocolDraftStore(str(tmp_path / "drafts.db"))
    restored = reopened.get(first.draft_id)
    assert restored is not None
    assert restored.yaml_text == _YAML_A
    reopened.close()


def test_sqlite_revision_persists_across_reopen(tmp_path: Path) -> None:
    db_path = tmp_path / "drafts.db"
    store = SqliteProtocolDraftStore(str(db_path))
    record = store.create("example-project", "demo", _YAML_A, _DIGEST_A, "key-1")
    draft_id = record.draft_id
    store.save(
        draft_id,
        yaml_text=_YAML_B,
        source_digest=_DIGEST_B,
        expected_revision=1,
        idempotency_key="key-2",
    )
    store.close()

    reopened = SqliteProtocolDraftStore(str(db_path))
    latest = reopened.get(draft_id)
    assert latest is not None
    assert latest.revision == 2
    first = reopened.get_revision(draft_id, 1)
    assert first is not None
    assert first.yaml_text == _YAML_A
    reopened.close()
