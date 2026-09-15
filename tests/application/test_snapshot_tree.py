"""快照文件树与文件级 diff 的口径用例（PLAN-20260915-058 WP-A）。"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from packages.application.workspace.snapshot_tree import (
    SnapshotChange,
    SnapshotChangeKind,
    SnapshotFile,
    SnapshotTree,
    diff_snapshot_trees,
    snapshot_tree,
)

LEFT = "sha256:" + "a" * 64
RIGHT = "sha256:" + "b" * 64


def _write(root: Path, relative: str, payload: bytes) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)


def test_snapshot_tree_lists_regular_files_sorted_with_digests(tmp_path: Path) -> None:
    _write(tmp_path, "b.txt", b"two")
    _write(tmp_path, "nested/a.txt", b"one")
    _write(tmp_path, "nested/deep/c.bin", b"three")

    tree = snapshot_tree(tmp_path)

    assert [item.path for item in tree.files] == ["b.txt", "nested/a.txt", "nested/deep/c.bin"]
    assert tree.truncated is False
    first = tree.files[1]
    assert first.path == "nested/a.txt"
    assert first.size_bytes == 3
    assert first.sha256 == hashlib.sha256(b"one").hexdigest()


def test_snapshot_tree_skips_symlinks(tmp_path: Path) -> None:
    _write(tmp_path, "real.txt", b"payload")
    secret = tmp_path.parent / "outside-secret.txt"
    secret.write_bytes(b"secret")
    try:
        (tmp_path / "link.txt").symlink_to(secret)
    except (OSError, NotImplementedError) as exc:  # pragma: no cover - 平台权限相关
        pytest.skip(f"symlink creation not permitted: {exc}")

    tree = snapshot_tree(tmp_path)

    assert [item.path for item in tree.files] == ["real.txt"]


def test_snapshot_tree_marks_truncation_instead_of_silent_prefix(tmp_path: Path) -> None:
    for index in range(5):
        _write(tmp_path, f"f{index}.txt", b"x")

    tree = snapshot_tree(tmp_path, limit=3)

    assert len(tree.files) == 3
    assert tree.truncated is True


def test_snapshot_file_rejects_escaping_paths() -> None:
    with pytest.raises(ValueError):
        SnapshotFile(path="../escape.txt", size_bytes=1, sha256="0" * 64)
    with pytest.raises(ValueError):
        SnapshotFile(path="/absolute.txt", size_bytes=1, sha256="0" * 64)


def test_diff_reports_added_removed_changed_and_unchanged(tmp_path: Path) -> None:
    before, after = tmp_path / "before", tmp_path / "after"
    _write(before, "keep.txt", b"same")
    _write(after, "keep.txt", b"same")
    _write(before, "gone.txt", b"bye")
    _write(after, "new.txt", b"hi")
    _write(before, "edit.txt", b"aaaa")
    _write(after, "edit.txt", b"bbbb")

    diff = diff_snapshot_trees(
        snapshot_tree(before), snapshot_tree(after), left_digest=LEFT, right_digest=RIGHT
    )

    kinds = {item.path: item.kind for item in diff.changes}
    assert kinds == {
        "edit.txt": SnapshotChangeKind.CHANGED,
        "gone.txt": SnapshotChangeKind.REMOVED,
        "new.txt": SnapshotChangeKind.ADDED,
    }
    assert [item.path for item in diff.changes] == ["edit.txt", "gone.txt", "new.txt"]
    assert (diff.added, diff.removed, diff.changed, diff.unchanged) == (1, 1, 1, 1)
    assert diff.identical is False
    assert diff.truncated is False


def test_diff_detects_same_length_rewrite(tmp_path: Path) -> None:
    """只比大小会漏掉同长度改写，所以变化判定必须用 sha256。"""

    before, after = tmp_path / "before", tmp_path / "after"
    _write(before, "same-size.txt", b"abcd")
    _write(after, "same-size.txt", b"abce")

    diff = diff_snapshot_trees(
        snapshot_tree(before), snapshot_tree(after), left_digest=LEFT, right_digest=RIGHT
    )

    assert diff.changed == 1
    change = diff.changes[0]
    assert change.left is not None and change.right is not None
    assert change.left.size_bytes == change.right.size_bytes == 4
    assert change.left.sha256 != change.right.sha256


def test_diff_of_identical_trees_carries_no_changes(tmp_path: Path) -> None:
    _write(tmp_path, "a.txt", b"payload")

    diff = diff_snapshot_trees(
        snapshot_tree(tmp_path), snapshot_tree(tmp_path), left_digest=LEFT, right_digest=RIGHT
    )

    assert diff.identical is True
    assert diff.changes == ()
    assert diff.unchanged == 1


def test_diff_marks_truncated_when_either_side_truncated() -> None:
    truncated = SnapshotTree(
        files=(SnapshotFile(path="a.txt", size_bytes=1, sha256="0" * 64),), truncated=True
    )
    full = SnapshotTree(files=(SnapshotFile(path="a.txt", size_bytes=1, sha256="0" * 64),))

    diff = diff_snapshot_trees(truncated, full, left_digest=LEFT, right_digest=RIGHT)

    assert diff.truncated is True


def test_change_requires_the_matching_side_only() -> None:
    item = SnapshotFile(path="a.txt", size_bytes=1, sha256="0" * 64)

    assert (
        SnapshotChange(path="a.txt", kind=SnapshotChangeKind.ADDED, left=None, right=item).right
        is item
    )
    with pytest.raises(ValueError):
        SnapshotChange(path="a.txt", kind=SnapshotChangeKind.ADDED, left=item, right=item)
    with pytest.raises(ValueError):
        SnapshotChange(path="a.txt", kind=SnapshotChangeKind.CHANGED, left=item, right=item)
