"""MemoryStore Port：Memory 持久化与写入门禁（CONTEXT_ENGINE.md §6、ADR-0017）。

职责：commit(MemoryWriteProposal) 执行 provenance/policy gate 后写入
MemoryRecord；读取/查询/删除；删除时协调 derived index 重建（索引是
derived，不是 canonical）。非职责：不做记忆语义判断（curator/gate 策略
由调用方 application/domain 提供）；向量索引本身（derived projection）。

M5 决策 D2：同步语义；gate 拒绝必须给出可分类失败（InvalidInputError）。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.domain.enums import MemoryTier
from packages.domain.memory import MemoryRecord, MemoryWriteProposal


@runtime_checkable
class MemoryStore(Protocol):
    """Memory 写入/读取/删除契约。"""

    def commit(self, proposal: MemoryWriteProposal) -> MemoryRecord: ...

    def get(self, memory_id: str) -> MemoryRecord: ...

    def query(self, tier: MemoryTier | None = None) -> tuple[MemoryRecord, ...]: ...

    def delete(self, memory_id: str) -> None: ...

    def close(self) -> None: ...
