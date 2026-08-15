"""Consistency checker 测试：5 类 drift 检测 + 只读性 + rebuild 收敛。

覆盖 M10 Scope drift 检测：missing projection、orphan projection、
stale version、deleted still indexed、nonexistent identity；
checker 不得反向修改 canonical。
"""

from __future__ import annotations

from dataclasses import replace

from adapters.fakes import FakeMemoryStore, FakeRetrievalIndex
from packages.application.memory.consistency import (
    check_index_consistency,
    rebuild_index,
)
from tests.contracts.fixtures import memory_proposal


def _store_with(*ids: str) -> FakeMemoryStore:
    store = FakeMemoryStore(allowed_sources=("source:article-1",))
    for memory_id in ids:
        store.commit(memory_proposal(memory_id))
    return store


class TestCleanState:
    def test_consistent_projection_reports_clean(self) -> None:
        store = _store_with("mem-1", "mem-2")
        canonical = store.query()
        index = FakeRetrievalIndex()
        index.rebuild(canonical)
        report = check_index_consistency(canonical, index)
        assert report.is_clean()


class TestMissingProjection:
    def test_active_record_without_projection_detected(self) -> None:
        store = _store_with("mem-1", "mem-2")
        canonical = store.query()
        index = FakeRetrievalIndex()
        index.rebuild((canonical[0],))
        report = check_index_consistency(canonical, index)
        assert report.missing_projection == ("mem-2",)


class TestOrphanAndNonexistent:
    def test_orphan_projection_detected(self) -> None:
        store = _store_with("mem-1")
        canonical = store.query()
        index = FakeRetrievalIndex()
        index.rebuild(canonical)
        index.upsert(replace(store.get("mem-1"), id="mem-ghost"))
        report = check_index_consistency(canonical, index)
        assert "mem-ghost" in report.orphan_projection
        assert "mem-ghost" in report.nonexistent_identity


class TestStaleVersion:
    def test_stale_hash_detected(self) -> None:
        store = _store_with("mem-1")
        canonical = store.query()
        index = FakeRetrievalIndex()
        index.rebuild(canonical)
        # 模拟投影漂移：内容变更但索引未更新（stale hash）
        updated = replace(store.get("mem-1"), content="changed content")
        stale_record = replace(store.get("mem-1"))
        index.rebuild((stale_record,))
        stale_canonical = (updated,)
        report = check_index_consistency(stale_canonical, index)
        assert "mem-1" in report.stale_version


class TestDeletedStillIndexed:
    def test_tombstone_still_indexed_detected(self) -> None:
        store = _store_with("mem-1", "mem-2")
        index = FakeRetrievalIndex()
        index.rebuild(store.query())  # 索引含 mem-1（active）
        # 故障注入：canonical deactivate 后索引未同步 remove
        store.deactivate("mem-1")
        canonical = store.query()
        report = check_index_consistency(canonical, index)
        assert "mem-1" in report.deleted_still_indexed


class TestReadOnlyGuarantee:
    def test_checker_does_not_modify_canonical(self) -> None:
        store = _store_with("mem-1")
        canonical = store.query()
        before = {record.id: (record.content, record.active) for record in canonical}
        index = FakeRetrievalIndex()
        index.rebuild(canonical)
        index.upsert(replace(store.get("mem-1"), id="mem-ghost"))
        check_index_consistency(canonical, index)
        after = {record.id: (record.content, record.active) for record in canonical}
        assert before == after


class TestRebuildConvergence:
    def test_rebuild_converges_all_drift(self) -> None:
        store = _store_with("mem-1", "mem-2", "mem-3")
        canonical = store.query()
        index = FakeRetrievalIndex()
        index.rebuild((canonical[0],))
        index.upsert(replace(canonical[0], id="mem-ghost"))
        report = check_index_consistency(canonical, index)
        assert report.drift_count > 0
        rebuild_index(canonical, index)
        assert check_index_consistency(canonical, index).is_clean()
