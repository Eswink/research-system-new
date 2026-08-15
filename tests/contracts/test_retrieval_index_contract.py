"""RetrievalIndex 契约测试：rebuild/upsert/remove/search/clear 语义。

覆盖：rebuild 只索引 active 记录、clear 后重建等价、delete 传播
（canonical deactivate 后索引不含该 id）、close 语义。
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from adapters.fakes import FakeMemoryStore
from adapters.index.in_memory_index import InMemoryRetrievalIndex
from packages.application.ports.errors import InvalidInputError, PermanentPortError
from packages.domain.memory import MemoryRecord
from tests.contracts.fixtures import memory_proposal


def _record(memory_id: str = "mem-1", content: str = "alpha beta") -> MemoryRecord:
    store = FakeMemoryStore(allowed_sources=("source:article-1",))
    record = store.commit(memory_proposal(memory_id))
    return replace(record, content=content)


class TestRetrievalIndexContract:
    def test_rebuild_indexes_only_active_records(self) -> None:
        index = InMemoryRetrievalIndex()
        active = _record("mem-1", "alpha beta")
        inactive = replace(_record("mem-2", "gamma delta"), active=False)
        index.rebuild((active, inactive))
        assert {entry.memory_id for entry in index.entries()} == {"mem-1"}

    def test_upsert_inactive_removes_entry(self) -> None:
        index = InMemoryRetrievalIndex()
        record = _record("mem-1")
        index.upsert(record)
        index.upsert(replace(record, active=False))
        assert index.entries() == ()

    def test_remove_unknown_is_noop(self) -> None:
        index = InMemoryRetrievalIndex()
        index.remove("missing")
        assert index.entries() == ()

    def test_search_returns_deterministic_token_matches(self) -> None:
        index = InMemoryRetrievalIndex()
        index.rebuild((_record("mem-1", "alpha beta"), _record("mem-2", "gamma delta")))
        hits = index.search("beta")
        assert [hit.memory_id for hit in hits] == ["mem-1"]
        assert hits[0].score == 1.0

    def test_clear_then_rebuild_is_equivalent(self) -> None:
        index = InMemoryRetrievalIndex()
        records = (_record("mem-1", "alpha"), _record("mem-2", "beta"))
        index.rebuild(records)
        before = {entry.memory_id: entry.content_hash for entry in index.entries()}
        index.clear()
        assert index.entries() == ()
        index.rebuild(records)
        after = {entry.memory_id: entry.content_hash for entry in index.entries()}
        assert before == after

    def test_delete_propagation_removes_from_index(self) -> None:
        index = InMemoryRetrievalIndex()
        record = _record("mem-1")
        index.rebuild((record,))
        index.remove("mem-1")
        assert index.entries() == ()

    def test_close_then_calls_rejected(self) -> None:
        index = InMemoryRetrievalIndex()
        index.close()
        with pytest.raises(PermanentPortError):
            index.search("probe")

    def test_negative_limit_rejected(self) -> None:
        index = InMemoryRetrievalIndex()
        with pytest.raises(InvalidInputError):
            index.search("probe", limit=-1)
