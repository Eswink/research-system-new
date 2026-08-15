"""MemoryStore Port：Memory 持久化与写入门禁（CONTEXT_ENGINE.md §6、ADR-0017）。

职责：commit(MemoryWriteProposal) 执行 provenance/policy gate 后写入
MemoryRecord；读取/查询/deactivate（canonical tombstone：active=False，
保留审计历史）/delete（物理移除）；删除时协调 derived index 重建
（索引是 derived，不是 canonical）。非职责：不做记忆语义判断
（curator/gate 策略由调用方 application/domain 提供）；向量索引本身
（derived projection）。

M5 决策 D2：同步语义；gate 拒绝必须给出可分类失败（InvalidInputError）。
M10 扩展：deactivate 表达 canonical 生命周期（supersede/删除的
tombstone 语义），与 delete（物理移除）区分。

M10 复审强化（实现必须一致遵守，contract suite 强制）：
- 未授权 provenance 的 commit 必须拒绝；
- 同 id 重复 commit 必须拒绝（防静默覆盖与重复事件），
  幂等由上层 proposal idempotency 管理。
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

    def deactivate(self, memory_id: str) -> MemoryRecord: ...

    def delete(self, memory_id: str) -> None: ...

    def close(self) -> None: ...
