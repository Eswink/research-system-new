"""ProtocolSource：协议来源的领域值对象（受控模板路径 **或** 草稿不可变修订）。

M12 队列（`ExperimentQueueEntry.source`）与 ResearchRun（`run.protocol_source`）
共用同一个值对象：来源是"这份 run 是用哪份协议装配出来的"这一事实，装配链
（`load_protocol_for_source` → Compile → Preflight → Freeze）对两种来源完全同源。

为什么把来源落成事实而不是协议正文副本：正文会漂移，来源可重解析——重启/续跑
时按来源重新装配，与首次启动走同一条链；解析不出来（路径消失、修订不存在）时
诚实拒绝，而不是静默换一份协议。
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["ProtocolSource"]


@dataclass(frozen=True, slots=True)
class ProtocolSource:
    """冻结的协议来源：受控模板路径或草稿修订（互斥）。"""

    protocol_path: str | None = None
    draft_id: str | None = None
    draft_revision: int | None = None

    def __post_init__(self) -> None:
        has_path = self.protocol_path is not None
        has_draft = self.draft_id is not None or self.draft_revision is not None
        if has_path == has_draft:
            raise ValueError(
                "exactly one protocol source required: protocol_path xor draft revision"
            )
        if has_path and not self.protocol_path:
            raise ValueError("protocol_path must not be empty when provided")
        if has_draft:
            if not self.draft_id:
                raise ValueError("draft source requires a non-empty draft_id")
            if self.draft_revision is None or self.draft_revision < 1:
                raise ValueError("draft source requires a positive draft_revision")

    @property
    def draft_ref(self) -> tuple[str, int] | None:
        """草稿来源的 (draft_id, revision)；路径来源为 None。"""
        if self.draft_id is None or self.draft_revision is None:
            return None
        return (self.draft_id, self.draft_revision)
