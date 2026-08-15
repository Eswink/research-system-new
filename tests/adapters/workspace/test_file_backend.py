"""FileWorkspaceBackend 测试（真实目录 + lease + 内容寻址 snapshot）。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from adapters.workspace import FileWorkspaceBackend, workspace_tree_digest
from packages.application.ports.errors import InvalidInputError, PermanentPortError
from packages.domain.workspace import Workspace

_EPOCH = datetime(2026, 8, 15, tzinfo=timezone.utc)


def _workspace(name: str = "ws-a") -> Workspace:
    return Workspace(id="ws-a", name=name)


class _Clock:
    def __init__(self) -> None:
        self.current = _EPOCH

    def __call__(self) -> datetime:
        return self.current

    def advance(self, seconds: int) -> None:
        self.current += timedelta(seconds=seconds)


def _backend(tmp_path: Path, ttl: int = 3600) -> tuple[FileWorkspaceBackend, _Clock]:
    clock = _Clock()
    backend = FileWorkspaceBackend(tmp_path / "root", lease_ttl_seconds=ttl, now=clock)
    return backend, clock


class TestCreateAndLease:
    def test_create_and_acquire(self, tmp_path: Path) -> None:
        backend, _ = _backend(tmp_path)
        workspace = _workspace()
        backend.create_workspace(workspace)
        lease = backend.acquire_lease(workspace, "session-1")
        assert lease.workspace_id == "ws-a"
        assert lease.agent_session_id == "session-1"
        assert lease.expires_at is not None
        assert (tmp_path / "root" / "ws-a").is_dir()

    def test_acquire_unknown_workspace_rejected(self, tmp_path: Path) -> None:
        backend, _ = _backend(tmp_path)
        with pytest.raises(InvalidInputError):
            backend.acquire_lease(_workspace(), "session-1")


class TestPathTraversalRejection:
    """workspace_id 路径穿越攻击必须被拒绝（安全边界）。"""

    @pytest.mark.parametrize(
        "evil_id",
        [
            "../../evil-outside",
            "..\\..\\evil-outside",
            "..",
            "a/b",
            "a\\b",
            "C:\\abs-outside",
            "/abs-outside",
        ],
    )
    def test_unsafe_workspace_id_rejected(self, tmp_path: Path, evil_id: str) -> None:
        backend, _ = _backend(tmp_path)
        with pytest.raises(InvalidInputError):
            backend.create_workspace(Workspace(id=evil_id, name="evil"))

    def test_rejected_id_creates_nothing_outside_root(self, tmp_path: Path) -> None:
        backend, _ = _backend(tmp_path)
        root = tmp_path / "root"
        with pytest.raises(InvalidInputError):
            backend.create_workspace(Workspace(id="../../evil-outside", name="evil"))
        assert not (tmp_path / "evil-outside").exists()
        assert list(root.iterdir()) == []

    def test_lease_expiry_rejects_operations(self, tmp_path: Path) -> None:
        backend, clock = _backend(tmp_path, ttl=60)
        workspace = _workspace()
        backend.create_workspace(workspace)
        lease = backend.acquire_lease(workspace, "session-1")
        clock.advance(61)
        with pytest.raises(InvalidInputError):
            backend.snapshot(lease)

    def test_renew_extends_lease(self, tmp_path: Path) -> None:
        backend, clock = _backend(tmp_path, ttl=60)
        workspace = _workspace()
        backend.create_workspace(workspace)
        lease = backend.acquire_lease(workspace, "session-1")
        clock.advance(30)
        lease = backend.renew_lease(lease)
        clock.advance(40)
        backend.snapshot(lease)

    def test_release_removes_lease(self, tmp_path: Path) -> None:
        backend, _ = _backend(tmp_path)
        workspace = _workspace()
        backend.create_workspace(workspace)
        lease = backend.acquire_lease(workspace, "session-1")
        backend.release_lease(lease)
        with pytest.raises(InvalidInputError):
            backend.snapshot(lease)

    def test_close_rejects_calls(self, tmp_path: Path) -> None:
        backend, _ = _backend(tmp_path)
        backend.close()
        with pytest.raises(PermanentPortError):
            backend.create_workspace(_workspace())


class TestSnapshot:
    def test_snapshot_digest_is_content_based(self, tmp_path: Path) -> None:
        backend, _ = _backend(tmp_path)
        workspace = _workspace()
        backend.create_workspace(workspace)
        lease = backend.acquire_lease(workspace, "session-1")
        workspace_dir = backend.workspace_dir(lease)
        (workspace_dir / "a.txt").write_text("hello", encoding="utf-8")
        snapshot = backend.snapshot(lease)
        assert snapshot.digest.startswith("sha256:")
        assert snapshot.digest == workspace_tree_digest(workspace_dir)

    def test_same_content_same_digest(self, tmp_path: Path) -> None:
        backend, _ = _backend(tmp_path)
        workspace = _workspace()
        backend.create_workspace(workspace)
        lease = backend.acquire_lease(workspace, "session-1")
        workspace_dir = backend.workspace_dir(lease)
        (workspace_dir / "a.txt").write_text("hello", encoding="utf-8")
        first = backend.snapshot(lease)
        second = backend.snapshot(lease)
        assert first.digest == second.digest

    def test_content_change_changes_digest(self, tmp_path: Path) -> None:
        backend, _ = _backend(tmp_path)
        workspace = _workspace()
        backend.create_workspace(workspace)
        lease = backend.acquire_lease(workspace, "session-1")
        workspace_dir = backend.workspace_dir(lease)
        (workspace_dir / "a.txt").write_text("hello", encoding="utf-8")
        first = backend.snapshot(lease)
        (workspace_dir / "a.txt").write_text("world", encoding="utf-8")
        second = backend.snapshot(lease)
        assert first.digest != second.digest

    def test_restore_replaces_workspace(self, tmp_path: Path) -> None:
        backend, _ = _backend(tmp_path)
        workspace = _workspace()
        backend.create_workspace(workspace)
        lease = backend.acquire_lease(workspace, "session-1")
        workspace_dir = backend.workspace_dir(lease)
        (workspace_dir / "a.txt").write_text("v1", encoding="utf-8")
        snapshot = backend.snapshot(lease)
        (workspace_dir / "a.txt").write_text("v2", encoding="utf-8")
        (workspace_dir / "b.txt").write_text("extra", encoding="utf-8")
        backend.restore(lease, snapshot)
        assert (workspace_dir / "a.txt").read_text(encoding="utf-8") == "v1"
        assert not (workspace_dir / "b.txt").exists()

    def test_merge_overlays_snapshot_files(self, tmp_path: Path) -> None:
        backend, _ = _backend(tmp_path)
        workspace = _workspace()
        backend.create_workspace(workspace)
        lease = backend.acquire_lease(workspace, "session-1")
        workspace_dir = backend.workspace_dir(lease)
        (workspace_dir / "a.txt").write_text("v1", encoding="utf-8")
        snapshot = backend.snapshot(lease)
        (workspace_dir / "a.txt").write_text("v2", encoding="utf-8")
        (workspace_dir / "b.txt").write_text("local", encoding="utf-8")
        backend.merge(lease, snapshot)
        assert (workspace_dir / "a.txt").read_text(encoding="utf-8") == "v1"
        assert (workspace_dir / "b.txt").read_text(encoding="utf-8") == "local"

    def test_unknown_snapshot_rejected(self, tmp_path: Path) -> None:
        backend, _ = _backend(tmp_path)
        workspace = _workspace()
        backend.create_workspace(workspace)
        lease = backend.acquire_lease(workspace, "session-1")
        from packages.domain.workspace import WorkspaceSnapshot

        ghost = WorkspaceSnapshot(workspace_id="ws-a", digest="sha256:" + "00" * 32)
        with pytest.raises(InvalidInputError):
            backend.restore(lease, ghost)
        with pytest.raises(InvalidInputError):
            backend.merge(lease, ghost)
