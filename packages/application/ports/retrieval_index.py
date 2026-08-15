"""RetrievalIndex Port：Memory 的 derived retrieval projection（M10 Scope）。

依据 ADR-0017 / AGENTS.md §8：向量/检索索引是 disposable projection，
绝不承载 canonical truth（ADR-0002 边界）；可清空、可重建、可更换
backend，而不改变 Canonical State。不绑定具体 embedding model 或
向量数据库（实现负责，Domain/Port 不感知）。

职责：rebuild（全量重建投影）/ upsert / remove / search /
entries（等价性校验视图）/ clear。非职责：不做 Memory 写入门禁；
不做 Canonical State 持久化。
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from packages.domain.memory import MemoryRecord


def content_hash_of(record: MemoryRecord) -> str:
    """MemoryRecord 内容哈希（active 状态敏感：tombstone 变化可检测）。

    供一致性 checker 与实现共用；是 derived projection 的等价性
    契约，不属于任何具体 adapter。
    """
    payload = f"{record.id}|{record.content}|{record.active}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class IndexEntry:
    """投影条目：canonical 身份的派生视图（等价性校验用）。"""

    memory_id: str
    content_hash: str


@dataclass(frozen=True, slots=True)
class IndexHit:
    """检索命中：memory id + 确定性评分。"""

    memory_id: str
    score: float


@runtime_checkable
class RetrievalIndex(Protocol):
    """Memory 检索投影契约；任何实现必须满足可重建与等价语义。"""

    def rebuild(self, records: tuple[MemoryRecord, ...]) -> None: ...

    def upsert(self, record: MemoryRecord) -> None: ...

    def remove(self, memory_id: str) -> None: ...

    def search(self, query: str, limit: int = 10) -> tuple[IndexHit, ...]: ...

    def entries(self) -> tuple[IndexEntry, ...]: ...

    def clear(self) -> None: ...

    def close(self) -> None: ...
