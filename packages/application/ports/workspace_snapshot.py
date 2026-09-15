"""WorkspaceSnapshotReader Port：按 digest 读取**保留中**的工作区快照（PLAN-20260915-058）。

职责：把内容寻址的快照 digest 解析成可枚举的文件清单，供控制面只读呈现。
非职责：不创建/恢复/合并/删除快照（那是 `WorkspaceBackend`），不获取 lease
（读取不写工作区），不解释快照的业务语义。

诚实边界：只读"确实存在于快照存储中的 digest"。未知 digest 必须抛
`InvalidInputError`（控制面映射 404），**不得**返回空树冒充"没有文件"。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.application.workspace.snapshot_tree import SnapshotTree


@runtime_checkable
class WorkspaceSnapshotReader(Protocol):
    """内容寻址快照的只读枚举能力（独立于 WorkspaceBackend 契约）。"""

    def retained_digests(self) -> frozenset[str]:
        """当前存储中保留的快照 digest 集合（无序；仅 `sha256:<hex>` 形式）。"""
        ...

    def snapshot_files(self, digest: str) -> SnapshotTree:
        """枚举某个保留中快照的文件清单。

        digest 非法或未保留时抛 `InvalidInputError`；树内出现 symlink 时抛
        `PermanentPortError`（快照存储被污染，不跟随链接读取宿主文件）。
        """
        ...
