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

from packages.domain.core import Digest

__all__ = ["ProtocolBody", "ProtocolSource"]


@dataclass(frozen=True, slots=True)
class ProtocolBody:
    """冻结的协议正文：启动时**被解析的那份字节** + 它的 sha256。

    为什么冻结正文而不是"重启时再解析一次来源"：来源（受控模板文件 / 草稿修订行）
    会消失，而"这份 run 是用哪份字节装配的"是 run 自己必须记得的事实——续跑不该
    因为外部文件被删/被改而失去重建入口（GOAL-004 cycle 1 / RECHECK-083 W-3）。

    值对象不变量：`digest` 必须是 `text` 的 sha256（篡改的正文构造不出来）。
    正文本身**不是**信任输入——重建仍要过语义 digest 校验（plan/catalog/契约漂移
    一律拒绝），冻结只是把同一份输入持久化，不新增放行路径。
    """

    text: str
    digest: Digest

    def __post_init__(self) -> None:
        if not self.text:
            raise ValueError("protocol body must not be empty")
        if Digest.of_bytes(self.text.encode("utf-8")) != self.digest:
            raise ValueError("protocol body digest does not match its text")

    @classmethod
    def of(cls, text: str) -> ProtocolBody:
        """按正文计算 digest（唯一的构造入口，杜绝"手填 digest"）。"""
        return cls(text=text, digest=Digest.of_bytes(text.encode("utf-8")))


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
