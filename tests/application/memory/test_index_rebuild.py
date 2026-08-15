"""删除后索引重建一致性测试（M10 DoD 2）。

覆盖：canonical → rebuild → 等价投影；delete/deactivate 后索引无
ghost retrieval；重建后仍一致（tombstone 不索引）。
"""

from __future__ import annotations

from adapters.fakes import FakeMemoryStore, FakeRetrievalIndex
from packages.application.memory.lifecycle import (
    MemoryLifecycleDeps,
    deactivate_memory,
    delete_memory,
)
from packages.domain.memory import MemoryRecord
from tests.contracts.fixtures import memory_proposal


def _records(*ids: str) -> tuple[MemoryRecord, ...]:
    store = FakeMemoryStore(allowed_sources=("source:article-1",))
    return tuple(store.commit(memory_proposal(memory_id)) for memory_id in ids)


class TestRebuildEquivalence:
    def test_clear_then_rebuild_is_equivalent(self) -> None:
        index = FakeRetrievalIndex()
        records = _records("mem-1", "mem-2", "mem-3")
        index.rebuild(records)
        before = {entry.memory_id: entry.content_hash for entry in index.entries()}
        index.clear()
        assert index.entries() == ()
        index.rebuild(records)
        after = {entry.memory_id: entry.content_hash for entry in index.entries()}
        assert before == after
        assert set(before) == {"mem-1", "mem-2", "mem-3"}

    def test_rebuild_idempotent(self) -> None:
        index = FakeRetrievalIndex()
        records = _records("mem-1", "mem-2")
        index.rebuild(records)
        first = index.entries()
        index.rebuild(records)
        assert first == index.entries()


class TestDeletePropagation:
    def test_delete_removes_index_entry(self) -> None:
        store = FakeMemoryStore(allowed_sources=("source:article-1",))
        index = FakeRetrievalIndex()
        records = _records("mem-1", "mem-2")
        store.commit(memory_proposal("mem-1"))
        store.commit(memory_proposal("mem-2"))
        index.rebuild(records)
        delete_memory(MemoryLifecycleDeps(store=store, index=index), "mem-1")
        assert {entry.memory_id for entry in index.entries()} == {"mem-2"}

    def test_deactivate_removes_index_entry_and_rebuild_excludes_tombstone(self) -> None:
        store = FakeMemoryStore(allowed_sources=("source:article-1",))
        index = FakeRetrievalIndex()
        store.commit(memory_proposal("mem-1"))
        store.commit(memory_proposal("mem-2"))
        canonical = store.query()
        index.rebuild(canonical)
        deactivate_memory(MemoryLifecycleDeps(store=store, index=index), "mem-1")
        assert {entry.memory_id for entry in index.entries()} == {"mem-2"}
        # canonical 含 tombstone（active=False），重建后仍不索引
        index.rebuild(store.query())
        assert {entry.memory_id for entry in index.entries()} == {"mem-2"}

    def test_no_ghost_retrieval_after_delete(self) -> None:
        store = FakeMemoryStore(allowed_sources=("source:article-1",))
        index = FakeRetrievalIndex()
        record = store.commit(memory_proposal("mem-1"))
        index.rebuild((record,))
        delete_memory(MemoryLifecycleDeps(store=store, index=index), "mem-1")
        hits = index.search("verified")
        assert [hit.memory_id for hit in hits] == []

    def test_rebuild_after_delete_excludes_deleted_canonical(self) -> None:
        store = FakeMemoryStore(allowed_sources=("source:article-1",))
        index = FakeRetrievalIndex()
        store.commit(memory_proposal("mem-1"))
        store.commit(memory_proposal("mem-2"))
        index.rebuild(store.query())
        delete_memory(MemoryLifecycleDeps(store=store, index=index), "mem-1")
        index.rebuild(store.query())
        assert {entry.memory_id for entry in index.entries()} == {"mem-2"}


class TestFaultInjection:
    def test_cleared_index_is_empty_projection_until_rebuild(self) -> None:
        index = FakeRetrievalIndex()
        index.rebuild(_records("mem-1"))
        index.clear()
        assert index.entries() == ()
        assert index.search("fact") == ()
