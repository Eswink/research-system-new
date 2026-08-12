"""WorkspaceBackend Port：工作区生命周期（ADR-0006、WORKSPACE_RUNTIME.md）。

职责：工作区创建、Lease 获取/续期/释放、快照/恢复/合并；无 Lease 不得
写入（ADR-0006）。非职责：不执行命令（ExecutionBackend）；不管理工作区
内容的领域语义（domain Workspace/WorkspaceLease）。

M5 决策 D2：同步语义；Lease 过期与续期语义由实现保证，Fake 提供
deterministic 时钟（可注入 now）。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.domain.workspace import (
    Workspace,
    WorkspaceLease,
    WorkspaceSnapshot,
)


@runtime_checkable
class WorkspaceBackend(Protocol):
    """工作区与 Lease 生命周期。"""

    def create_workspace(self, workspace: Workspace) -> None: ...

    def acquire_lease(self, workspace: Workspace, agent_session_id: str) -> WorkspaceLease: ...

    def renew_lease(self, lease: WorkspaceLease) -> WorkspaceLease: ...

    def release_lease(self, lease: WorkspaceLease) -> None: ...

    def snapshot(self, lease: WorkspaceLease) -> WorkspaceSnapshot: ...

    def restore(self, lease: WorkspaceLease, snapshot: WorkspaceSnapshot) -> None: ...

    def merge(self, lease: WorkspaceLease, snapshot: WorkspaceSnapshot) -> None: ...

    def close(self) -> None: ...
