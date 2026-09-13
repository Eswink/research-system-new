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


class TestSymlinkRejection:
    """SA-1-M005：workspace 内 symlink 必须被拒绝，防止宿主文件经 snapshot 泄露。"""

    @staticmethod
    def _make_symlink(target: Path, link: Path) -> None:
        try:
            link.symlink_to(target)
        except OSError as exc:
            # Windows 非管理员/未开开发者模式时无法创建 symlink；跳过而非掩盖
            pytest.skip(f"symlink creation not permitted: {exc}")

    def test_snapshot_rejects_symlink(self, tmp_path: Path) -> None:
        backend, _ = _backend(tmp_path)
        workspace = _workspace()
        backend.create_workspace(workspace)
        lease = backend.acquire_lease(workspace, "session-1")
        workspace_dir = backend.workspace_dir(lease)
        secret = tmp_path / "outside-secret.txt"
        secret.write_text("host-content", encoding="utf-8")
        self._make_symlink(secret, workspace_dir / "link.txt")
        with pytest.raises(PermanentPortError):
            backend.snapshot(lease)
        # 拒绝后不得产生快照副本；.snapshots 是惰性目录，被拒绝时可能尚未创建。
        snapshots_root = tmp_path / "root" / ".snapshots"
        assert not snapshots_root.exists() or list(snapshots_root.iterdir()) == []

    def test_tree_digest_ignores_symlink(self, tmp_path: Path) -> None:
        backend, _ = _backend(tmp_path)
        workspace = _workspace()
        backend.create_workspace(workspace)
        lease = backend.acquire_lease(workspace, "session-1")
        workspace_dir = backend.workspace_dir(lease)
        (workspace_dir / "a.txt").write_text("hello", encoding="utf-8")
        digest_before = workspace_tree_digest(workspace_dir)
        secret = tmp_path / "outside.txt"
        secret.write_text("host-content", encoding="utf-8")
        self._make_symlink(secret, workspace_dir / "link.txt")
        digest_after = workspace_tree_digest(workspace_dir)
        assert digest_before == digest_after
        # 真实文件变化仍改变 digest（symlink 跳过不影响正常检测）
        (workspace_dir / "a.txt").write_text("world", encoding="utf-8")
        assert workspace_tree_digest(workspace_dir) != digest_before


class TestBundleTransfer:
    """M16 WP3: workspace bundle export/import with dual digest verification."""

    def _snapshotted(self, tmp_path: Path) -> tuple[FileWorkspaceBackend, object, str]:
        backend, _ = _backend(tmp_path)
        workspace = _workspace()
        backend.create_workspace(workspace)
        lease = backend.acquire_lease(workspace, "session-1")
        workspace_dir = backend.workspace_dir(lease)
        (workspace_dir / "a.txt").write_text("hello", encoding="utf-8")
        (workspace_dir / "sub" / "b.txt").parent.mkdir(parents=True, exist_ok=True)
        (workspace_dir / "sub" / "b.txt").write_text("nested", encoding="utf-8")
        snapshot = backend.snapshot(lease)
        return backend, lease, snapshot.digest

    def test_export_import_roundtrip_preserves_tree(self, tmp_path: Path) -> None:
        backend, _, digest = self._snapshotted(tmp_path)
        workspace = _workspace()
        lease = backend.acquire_lease(workspace, "session-1")
        bundle = backend.export_bundle(lease, backend.snapshot(lease))
        assert isinstance(bundle, bytes) and bundle
        # import into a fresh workspace id and verify tree digest
        backend.create_workspace(Workspace(id="ws-import", name="ws-import"))
        restored = backend.import_bundle("ws-import", bundle, digest)
        assert restored.digest == digest
        imported_dir = tmp_path / "root" / "ws-import"
        assert (imported_dir / "a.txt").read_text(encoding="utf-8") == "hello"
        assert (imported_dir / "sub" / "b.txt").read_text(encoding="utf-8") == "nested"

    def test_import_wrong_digest_rejected(self, tmp_path: Path) -> None:
        backend, _, digest = self._snapshotted(tmp_path)
        lease = backend.acquire_lease(_workspace(), "session-1")
        bundle = backend.export_bundle(lease, backend.snapshot(lease))
        backend.create_workspace(Workspace(id="ws-import", name="x"))
        with pytest.raises(InvalidInputError):
            backend.import_bundle("ws-import", bundle, "sha256:" + "11" * 32)
        # rejected import must not leave a materialized workspace behind
        assert not (tmp_path / "root" / "ws-import" / "a.txt").exists()

    def test_import_truncated_bundle_rejected(self, tmp_path: Path) -> None:
        backend, _, digest = self._snapshotted(tmp_path)
        lease = backend.acquire_lease(_workspace(), "session-1")
        bundle = backend.export_bundle(lease, backend.snapshot(lease))
        backend.create_workspace(Workspace(id="ws-import", name="x"))
        with pytest.raises(InvalidInputError):
            backend.import_bundle("ws-import", bundle[: len(bundle) // 2], digest)

    def test_import_malicious_traversal_bundle_rejected(self, tmp_path: Path) -> None:
        import base64
        import json

        from adapters.workspace.bundle import BundleError

        backend, _ = _backend(tmp_path)
        backend.create_workspace(Workspace(id="ws-import", name="x"))
        # hand-craft a bundle that encode_bundle would never emit
        evil = json.dumps(
            {
                "version": 1,
                "entries": [
                    {
                        "path": "../../escape.txt",
                        "sha256": "0" * 64,
                        "data_b64": base64.b64encode(b"pwned").decode(),
                    }
                ],
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        with pytest.raises((InvalidInputError, BundleError)):
            backend.import_bundle("ws-import", evil, "sha256:" + "22" * 32)
        assert not (tmp_path / "escape.txt").exists()


class TestBundleCodec:
    def test_encode_decode_roundtrip(self) -> None:
        from adapters.workspace.bundle import decode_bundle, encode_bundle

        entries = {"a.txt": b"one", "dir/b.txt": b"two"}
        decoded = decode_bundle(encode_bundle(entries))
        assert decoded == entries

    def test_decode_rejects_entry_digest_mismatch(self) -> None:
        import json

        from adapters.workspace.bundle import BundleError, decode_bundle

        bundle = json.dumps(
            {
                "version": 1,
                "entries": [{"path": "a.txt", "sha256": "0" * 64, "data_b64": "aGk="}],
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        with pytest.raises(BundleError):
            decode_bundle(bundle)

    def test_decode_rejects_non_canonical_json(self) -> None:
        from adapters.workspace.bundle import BundleError, decode_bundle

        with pytest.raises(BundleError):
            decode_bundle(b"not json")
