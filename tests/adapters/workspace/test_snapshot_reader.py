"""FileSnapshotReader 安全边界用例（PLAN-20260915-058 WP-B）。"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from adapters.workspace.snapshot_reader import FileSnapshotReader
from packages.application.ports.errors import InvalidInputError, PermanentPortError

DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64


def _snapshot_dir(root: Path, digest: str) -> Path:
    target = root / ".snapshots" / digest.split(":", 1)[1]
    target.mkdir(parents=True, exist_ok=True)
    return target


def _write(directory: Path, relative: str, payload: bytes) -> None:
    target = directory / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)


def test_retained_digests_lists_only_content_addressed_directories(tmp_path: Path) -> None:
    _write(_snapshot_dir(tmp_path, DIGEST_A), "a.txt", b"a")
    _write(_snapshot_dir(tmp_path, DIGEST_B), "b.txt", b"b")
    (tmp_path / ".snapshots" / "not-a-digest").mkdir()
    (tmp_path / "workspace-1").mkdir()

    reader = FileSnapshotReader(tmp_path)

    assert reader.retained_digests() == frozenset({DIGEST_A, DIGEST_B})


def test_retained_digests_is_empty_without_snapshot_store(tmp_path: Path) -> None:
    assert FileSnapshotReader(tmp_path).retained_digests() == frozenset()


def test_snapshot_files_returns_tree(tmp_path: Path) -> None:
    directory = _snapshot_dir(tmp_path, DIGEST_A)
    _write(directory, "nested/a.txt", b"one")
    _write(directory, "b.txt", b"two")

    tree = FileSnapshotReader(tmp_path).snapshot_files(DIGEST_A)

    assert [item.path for item in tree.files] == ["b.txt", "nested/a.txt"]
    assert tree.files[0].sha256 == hashlib.sha256(b"two").hexdigest()


@pytest.mark.parametrize(
    "digest",
    (
        "",
        "sha256:",
        "../escape",
        "sha256:" + "a" * 63,
        "sha256:" + "A" * 64,
        "md5:" + "a" * 32,
        "sha256:../../etc/passwd",
    ),
)
def test_snapshot_files_rejects_malformed_digest(tmp_path: Path, digest: str) -> None:
    reader = FileSnapshotReader(tmp_path)

    with pytest.raises(InvalidInputError):
        reader.snapshot_files(digest)


def test_snapshot_files_rejects_unretained_digest(tmp_path: Path) -> None:
    _write(_snapshot_dir(tmp_path, DIGEST_A), "a.txt", b"a")

    with pytest.raises(InvalidInputError):
        FileSnapshotReader(tmp_path).snapshot_files(DIGEST_B)


def test_snapshot_files_rejects_symlink_inside_snapshot(tmp_path: Path) -> None:
    directory = _snapshot_dir(tmp_path, DIGEST_A)
    _write(directory, "real.txt", b"payload")
    secret = tmp_path.parent / "outside.txt"
    secret.write_bytes(b"secret")
    try:
        (directory / "link.txt").symlink_to(secret)
    except (OSError, NotImplementedError) as exc:  # pragma: no cover - 平台权限相关
        pytest.skip(f"symlink creation not permitted: {exc}")

    with pytest.raises(PermanentPortError):
        FileSnapshotReader(tmp_path).snapshot_files(DIGEST_A)


def test_reader_ignores_workspace_directories(tmp_path: Path) -> None:
    """读取器只暴露 `.snapshots`，工作区目录内容不可通过本 Port 读取。"""
    workspace = tmp_path / "workspace-1"
    _write(workspace, "secret.txt", b"workspace content")
    _write(_snapshot_dir(tmp_path, DIGEST_A), "a.txt", b"a")

    reader = FileSnapshotReader(tmp_path)

    assert [item.path for item in reader.snapshot_files(DIGEST_A).files] == ["a.txt"]
    assert reader.retained_digests() == frozenset({DIGEST_A})
