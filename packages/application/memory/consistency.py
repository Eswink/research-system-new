"""Canonical Memory 与 derived index 的一致性检查（M10 Scope drift）。

检测 5 类 drift：
- missing_projection：active canonical 记录无对应投影；
- orphan_projection：投影 id 不存在于 canonical；
- stale_version：投影内容哈希与 canonical 记录不一致；
- deleted_still_indexed：canonical 已 inactive/tombstone 但仍被索引；
- nonexistent_identity：投影指向 canonical 不存在的 id（orphan 特例）。

Checker 是纯函数只读：绝不修改 canonical；修复路径 = 显式全量 rebuild。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.ports.retrieval_index import RetrievalIndex, content_hash_of
from packages.domain.memory import MemoryRecord


@dataclass(frozen=True, slots=True)
class DriftReport:
    missing_projection: tuple[str, ...] = ()
    orphan_projection: tuple[str, ...] = ()
    stale_version: tuple[str, ...] = ()
    deleted_still_indexed: tuple[str, ...] = ()
    nonexistent_identity: tuple[str, ...] = ()

    @property
    def drift_count(self) -> int:
        return (
            len(self.missing_projection)
            + len(self.orphan_projection)
            + len(self.stale_version)
            + len(self.deleted_still_indexed)
            + len(self.nonexistent_identity)
        )

    def is_clean(self) -> bool:
        return self.drift_count == 0


def check_index_consistency(
    canonical: tuple[MemoryRecord, ...],
    index: RetrievalIndex,
) -> DriftReport:
    """只读比较 canonical 与 index 投影；返回分类 DriftReport。"""
    canonical_ids = {record.id for record in canonical}
    active_records = {record.id: record for record in canonical if record.active}
    indexed = {entry.memory_id: entry.content_hash for entry in index.entries()}

    missing_projection = tuple(sorted(active_records.keys() - indexed.keys()))
    orphan_projection = tuple(sorted(indexed.keys() - canonical_ids))
    nonexistent_identity = orphan_projection
    stale_version = tuple(
        sorted(
            memory_id
            for memory_id, hash_value in indexed.items()
            if memory_id in active_records
            and hash_value != content_hash_of(active_records[memory_id])
        )
    )
    deleted_still_indexed = tuple(
        sorted(
            memory_id
            for memory_id in indexed
            if memory_id in canonical_ids
            and not next(record for record in canonical if record.id == memory_id).active
        )
    )
    return DriftReport(
        missing_projection=missing_projection,
        orphan_projection=orphan_projection,
        stale_version=stale_version,
        deleted_still_indexed=deleted_still_indexed,
        nonexistent_identity=nonexistent_identity,
    )


def rebuild_index(canonical: tuple[MemoryRecord, ...], index: RetrievalIndex) -> None:
    """显式修复路径：全量重建投影（不改 canonical）。"""
    index.rebuild(canonical)
