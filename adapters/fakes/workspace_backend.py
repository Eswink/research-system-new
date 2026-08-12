"""FakeWorkspaceBackend：工作区 + Lease 生命周期（deterministic 时钟）。"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from adapters.fakes.base import FakeBase
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import Timestamp
from packages.domain.workspace import (
    Workspace,
    WorkspaceLease,
    WorkspaceSnapshot,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FakeWorkspaceBackend(FakeBase):
    """create/lease/snapshot/restore/merge；Lease 过期后操作被拒绝。"""

    def __init__(
        self,
        *,
        lease_ttl_seconds: int = 3600,
        now: Callable[[], datetime] = _utc_now,
    ) -> None:
        super().__init__("workspace_backend")
        self._ttl = timedelta(seconds=lease_ttl_seconds)
        self._now = now
        self._workspaces: dict[str, Workspace] = {}
        self._leases: dict[str, WorkspaceLease] = {}
        self._snapshots: dict[str, WorkspaceSnapshot] = {}
        self._snapshot_counter = 0

    def create_workspace(self, workspace: Workspace) -> None:
        self._enter("create_workspace", workspace.id)
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

    def _active_lease(self, method: str, lease: WorkspaceLease) -> WorkspaceLease:
        stored = self._leases.get(lease.agent_session_id)
        if stored is None:
            self._record(method, lease.agent_session_id, error="InvalidInputError")
            raise InvalidInputError(f"no active lease for session {lease.agent_session_id}")
        if stored.expires_at is not None and stored.expires_at.value < self._now():
            self._record(method, lease.agent_session_id, error="InvalidInputError")
            raise InvalidInputError(f"lease expired for session {lease.agent_session_id}")
        return stored

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

    def _new_snapshot(self, lease: WorkspaceLease, digest: str) -> WorkspaceSnapshot:
        self._snapshot_counter += 1
        return WorkspaceSnapshot(
            workspace_id=lease.workspace_id,
            digest=digest,
            created_at=Timestamp(self._now()),
        )

    def snapshot(self, lease: WorkspaceLease) -> WorkspaceSnapshot:
        self._enter("snapshot", lease.workspace_id)
        self._active_lease("snapshot", lease)
        snapshot = self._new_snapshot(lease, f"snap-{self._snapshot_counter}")
        self._snapshots[snapshot.digest] = snapshot
        self._record("snapshot", lease.workspace_id, result=snapshot.digest)
        return snapshot

    def restore(self, lease: WorkspaceLease, snapshot: WorkspaceSnapshot) -> None:
        self._enter("restore", snapshot.digest)
        self._active_lease("restore", lease)
        if snapshot.digest not in self._snapshots:
            self._record("restore", snapshot.digest, error="InvalidInputError")
            raise InvalidInputError(f"unknown snapshot digest: {snapshot.digest}")
        self._record("restore", snapshot.digest)

    def merge(self, lease: WorkspaceLease, snapshot: WorkspaceSnapshot) -> None:
        self._enter("merge", snapshot.digest)
        self._active_lease("merge", lease)
        if snapshot.digest not in self._snapshots:
            self._record("merge", snapshot.digest, error="InvalidInputError")
            raise InvalidInputError(f"unknown snapshot digest: {snapshot.digest}")
        self._record("merge", snapshot.digest)
