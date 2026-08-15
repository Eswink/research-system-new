"""FileWorkspaceBackend：WorkspaceBackend Port 的真实文件系统实现（M9）。

职责：工作区目录生命周期（create/lease/renew/release/snapshot/restore/
merge）；无 Lease 不得写入（ADR-0006）。非职责：不执行命令
（ExecutionBackend）。snapshot digest 为真实内容寻址（确定性文件树
digest），可支撑容器挂载与 ReproducibilityAudit；Fake 的 `snap-N` 计数器
语义不在本实现中复刻。

实现细节：
- workspace 目录 = root / <workspace.id>（id 为 UUID 形式，安全路径）；
- snapshot 内容存 root/.snapshots/<digest_hex>/（内容寻址，重复快照跳过拷贝）；
- restore = 清空工作区后复制快照内容；merge = 快照文件覆盖到工作区
  （工作区独有文件保留）；
- lease 以 agent_session_id 为键，过期即拒绝（与 FakeWorkspaceBackend 语义一致）；
- call recording 为 contract suite 要求（tests/contracts registry 断言
  hasattr(instance, "calls")），只记摘要不记内容明文。
"""

from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from packages.application.ports.errors import InvalidInputError, PermanentPortError
from packages.application.ports.workspace_backend import WorkspaceBackend
from packages.domain.core import Timestamp
from packages.domain.enums import FailureCategory
from packages.domain.workspace import (
    Workspace,
    WorkspaceLease,
    WorkspaceSnapshot,
)

_CLOSED_ERROR = PermanentPortError(
    "workspace backend is closed",
    failure_category=FailureCategory.CONFIGURATION,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class _CallRecord:
    """一次调用的可审计摘要（不记录文件内容）。"""

    port: str
    method: str
    index: int
    args_summary: str
    result_summary: str | None = None
    error: str | None = None
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def workspace_tree_digest(directory: Path) -> str:
    """确定性目录内容 digest：排序 (relpath, sha256) 列表的 sha256。"""
    entries: list[tuple[str, str]] = []
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            rel = path.relative_to(directory).as_posix()
            entries.append((rel, hashlib.sha256(path.read_bytes()).hexdigest()))
    payload = json.dumps(entries, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


class FileWorkspaceBackend(WorkspaceBackend):
    """真实目录工作区 + Lease 生命周期 + 内容寻址 snapshot。"""

    def __init__(
        self,
        root: str | Path,
        *,
        lease_ttl_seconds: int = 3600,
        now: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._port = "workspace_backend"
        self._calls: list[_CallRecord] = []
        self._closed = False
        self._root = Path(root).resolve()
        self._ttl = timedelta(seconds=lease_ttl_seconds)
        self._now = now
        self._workspaces: dict[str, Workspace] = {}
        self._leases: dict[str, WorkspaceLease] = {}
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def calls(self) -> tuple[_CallRecord, ...]:
        return tuple(self._calls)

    def method_calls(self, method: str) -> int:
        return sum(1 for call in self._calls if call.method == method)

    def workspace_dir(self, lease: WorkspaceLease) -> Path:
        """租约工作区的宿主绝对路径（供 ExecutionSpec.workspace_path 挂载）。

        Port 契约不含此方法；它是 composition root 把容器挂载路径解析器
        注入 experiment use case 时的实现侧能力。
        """
        return self._dir_for(lease.workspace_id)

    def create_workspace(self, workspace: Workspace) -> None:
        self._enter("create_workspace", workspace.id)
        self._dir_for(workspace.id).mkdir(parents=True, exist_ok=True)
        self._workspaces[workspace.id] = workspace
        self._record("create_workspace", workspace.id)

    def acquire_lease(self, workspace: Workspace, agent_session_id: str) -> WorkspaceLease:
        self._enter("acquire_lease", workspace.id)
        if workspace.id not in self._workspaces:
            self._record("acquire_lease", workspace.id, error="InvalidInputError")
            raise InvalidInputError(f"unknown workspace: {workspace.id}")
        lease = WorkspaceLease(
            workspace_id=workspace.id,
            agent_session_id=agent_session_id,
            read_scopes=list(workspace.read_scopes),
            write_scopes=list(workspace.write_scopes),
            expires_at=Timestamp(self._now() + self._ttl),
            heartbeat=Timestamp(self._now()),
        )
        self._leases[lease.agent_session_id] = lease
        self._record("acquire_lease", workspace.id)
        return lease

    def renew_lease(self, lease: WorkspaceLease) -> WorkspaceLease:
        self._enter("renew_lease", lease.agent_session_id)
        current = self._active_lease("renew_lease", lease)
        renewed = WorkspaceLease(
            workspace_id=current.workspace_id,
            agent_session_id=current.agent_session_id,
            base_snapshot=current.base_snapshot,
            read_scopes=list(current.read_scopes),
            write_scopes=list(current.write_scopes),
            network_profile=current.network_profile,
            compute_profile=current.compute_profile,
            expires_at=Timestamp(self._now() + self._ttl),
            heartbeat=Timestamp(self._now()),
        )
        self._leases[renewed.agent_session_id] = renewed
        self._record("renew_lease", lease.agent_session_id)
        return renewed

    def release_lease(self, lease: WorkspaceLease) -> None:
        self._enter("release_lease", lease.agent_session_id)
        self._leases.pop(lease.agent_session_id, None)
        self._record("release_lease", lease.agent_session_id)

    def snapshot(self, lease: WorkspaceLease) -> WorkspaceSnapshot:
        self._enter("snapshot", lease.workspace_id)
        self._active_lease("snapshot", lease)
        source = self._dir_for(lease.workspace_id)
        digest = workspace_tree_digest(source)
        snapshot_dir = self._snapshots_root() / digest.split(":", 1)[1]
        if not snapshot_dir.exists():
            staged = snapshot_dir.with_name(snapshot_dir.name + ".staging")
            if staged.exists():
                shutil.rmtree(staged)
            shutil.copytree(source, staged)
            staged.replace(snapshot_dir)
        snapshot = WorkspaceSnapshot(
            workspace_id=lease.workspace_id,
            digest=digest,
            created_at=Timestamp(self._now()),
        )
        self._record("snapshot", lease.workspace_id, result=digest)
        return snapshot

    def restore(self, lease: WorkspaceLease, snapshot: WorkspaceSnapshot) -> None:
        self._enter("restore", snapshot.digest)
        self._active_lease("restore", lease)
        snapshot_dir = self._require_snapshot("restore", snapshot)
        target = self._dir_for(lease.workspace_id)
        shutil.rmtree(target)
        shutil.copytree(snapshot_dir, target)
        self._record("restore", snapshot.digest)

    def merge(self, lease: WorkspaceLease, snapshot: WorkspaceSnapshot) -> None:
        self._enter("merge", snapshot.digest)
        self._active_lease("merge", lease)
        snapshot_dir = self._require_snapshot("merge", snapshot)
        target = self._dir_for(lease.workspace_id)
        for source in sorted(snapshot_dir.rglob("*")):
            if not source.is_file():
                continue
            rel = source.relative_to(snapshot_dir)
            destination = target / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        self._record("merge", snapshot.digest)

    def close(self) -> None:
        self._closed = True

    def _enter(self, method: str, args_summary: str) -> None:
        if self._closed:
            self._record(method, args_summary, error="PermanentPortError")
            raise _CLOSED_ERROR

    def _record(
        self,
        method: str,
        args_summary: str,
        *,
        result: str | None = None,
        error: str | None = None,
    ) -> None:
        self._calls.append(
            _CallRecord(
                port=self._port,
                method=method,
                index=len(self._calls),
                args_summary=args_summary,
                result_summary=result,
                error=error,
            )
        )

    def _active_lease(self, method: str, lease: WorkspaceLease) -> WorkspaceLease:
        stored = self._leases.get(lease.agent_session_id)
        if stored is None:
            self._record(method, lease.agent_session_id, error="InvalidInputError")
            raise InvalidInputError(f"no active lease for session {lease.agent_session_id}")
        if stored.expires_at is not None and stored.expires_at.value < self._now():
            self._record(method, lease.agent_session_id, error="InvalidInputError")
            raise InvalidInputError(f"lease expired for session {lease.agent_session_id}")
        return stored

    def _dir_for(self, workspace_id: str) -> Path:
        return self._root / workspace_id

    def _snapshots_root(self) -> Path:
        return self._root / ".snapshots"

    def _require_snapshot(self, method: str, snapshot: WorkspaceSnapshot) -> Path:
        if not snapshot.digest.startswith("sha256:"):
            self._record(method, snapshot.digest, error="InvalidInputError")
            raise InvalidInputError(f"unknown snapshot digest: {snapshot.digest}")
        snapshot_dir = self._snapshots_root() / snapshot.digest.split(":", 1)[1]
        if not snapshot_dir.exists():
            self._record(method, snapshot.digest, error="InvalidInputError")
            raise InvalidInputError(f"unknown snapshot digest: {snapshot.digest}")
        return snapshot_dir
