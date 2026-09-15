"""工作区快照文件树与文件级 diff（PLAN-20260915-058 WP-A）。

口径：快照是**内容寻址**的工作区树（digest = 目录树摘要，见
`adapters/workspace/bundle.py`）。本模块只做两件事：把一棵快照树枚举成
(路径, 大小, sha256) 清单；把两份清单比成文件级差异（新增/删除/内容变化）。

诚实边界：

- 只枚举常规文件，符号链接不跟随（与快照写入侧的拒绝策略同口径）；
- 文件数超上限 → `truncated=True`，不假装清单完整；
- 文件级 diff **不做内容行级 diff**——内容 diff 由制品侧的
  `GET /artifacts/{a}/diff/{b}` 提供，两者不混用、不互相冒充；
- 只有 sha256 变化才算 CHANGED（只比大小会漏掉同长度改写）。
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

# 单次枚举的文件数上限（超出置 truncated，不静默丢弃）。
MAX_SNAPSHOT_FILES = 5000
_DIGEST_CHUNK_BYTES = 1024 * 1024


class SnapshotChangeKind(StrEnum):
    """快照之间单个路径的变化种类。"""

    ADDED = "ADDED"
    REMOVED = "REMOVED"
    CHANGED = "CHANGED"


@dataclass(frozen=True, slots=True)
class SnapshotFile:
    """快照中的一个常规文件（路径为 POSIX 相对路径）。"""

    path: str
    size_bytes: int
    sha256: str

    def __post_init__(self) -> None:
        if not self.path or self.path.startswith("/") or ".." in self.path.split("/"):
            raise ValueError(f"snapshot path must be a relative posix path: {self.path!r}")
        if self.size_bytes < 0:
            raise ValueError("snapshot file size must not be negative")


@dataclass(frozen=True, slots=True)
class SnapshotTree:
    """一棵快照树的枚举结果（truncated 时 files 只是前缀，不是全量）。"""

    files: tuple[SnapshotFile, ...]
    truncated: bool = False


@dataclass(frozen=True, slots=True)
class SnapshotChange:
    """一个路径在两个快照之间的变化；缺失一侧即新增/删除。"""

    path: str
    kind: SnapshotChangeKind
    left: SnapshotFile | None
    right: SnapshotFile | None

    def __post_init__(self) -> None:
        if self.kind is SnapshotChangeKind.ADDED and (self.left or self.right is None):
            raise ValueError("ADDED change must carry only the right side")
        if self.kind is SnapshotChangeKind.REMOVED and (self.right or self.left is None):
            raise ValueError("REMOVED change must carry only the left side")
        if self.kind is SnapshotChangeKind.CHANGED and (self.left is None or self.right is None):
            raise ValueError("CHANGED change must carry both sides")
        if self.kind is SnapshotChangeKind.CHANGED and self.left == self.right:
            raise ValueError("CHANGED change must differ between sides")


@dataclass(frozen=True, slots=True)
class SnapshotDiff:
    """两个快照的文件级差异（只比元数据，不比内容逐行）。"""

    left_digest: str
    right_digest: str
    changes: tuple[SnapshotChange, ...]
    added: int
    removed: int
    changed: int
    unchanged: int
    truncated: bool = False

    @property
    def identical(self) -> bool:
        return not self.changes


def snapshot_tree(directory: Path, *, limit: int = MAX_SNAPSHOT_FILES) -> SnapshotTree:
    """枚举目录树中的常规文件（符号链接不跟随），按路径排序。"""
    files: list[SnapshotFile] = []
    truncated = False
    for path in sorted(directory.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        if len(files) >= limit:
            truncated = True
            break
        relative = path.relative_to(directory).as_posix()
        files.append(
            SnapshotFile(
                path=relative,
                size_bytes=path.stat().st_size,
                sha256=_file_sha256(path),
            )
        )
    return SnapshotTree(files=tuple(files), truncated=truncated)


def diff_snapshot_trees(
    left: SnapshotTree,
    right: SnapshotTree,
    *,
    left_digest: str,
    right_digest: str,
) -> SnapshotDiff:
    """两份快照清单的文件级差异（纯函数；不读内容、不写任何持久面）。"""
    left_files = {item.path: item for item in left.files}
    right_files = {item.path: item for item in right.files}
    changes = [
        *_added_changes(left_files, right_files),
        *_removed_changes(left_files, right_files),
        *_changed_changes(left_files, right_files),
    ]
    changes.sort(key=lambda item: item.path)
    unchanged = sum(
        1
        for path, item in left_files.items()
        if path in right_files and right_files[path].sha256 == item.sha256
    )
    return SnapshotDiff(
        left_digest=left_digest,
        right_digest=right_digest,
        changes=tuple(changes),
        added=sum(1 for item in changes if item.kind is SnapshotChangeKind.ADDED),
        removed=sum(1 for item in changes if item.kind is SnapshotChangeKind.REMOVED),
        changed=sum(1 for item in changes if item.kind is SnapshotChangeKind.CHANGED),
        unchanged=unchanged,
        truncated=left.truncated or right.truncated,
    )


def _added_changes(
    left_files: dict[str, SnapshotFile], right_files: dict[str, SnapshotFile]
) -> list[SnapshotChange]:
    return [
        SnapshotChange(path=path, kind=SnapshotChangeKind.ADDED, left=None, right=item)
        for path, item in right_files.items()
        if path not in left_files
    ]


def _removed_changes(
    left_files: dict[str, SnapshotFile], right_files: dict[str, SnapshotFile]
) -> list[SnapshotChange]:
    return [
        SnapshotChange(path=path, kind=SnapshotChangeKind.REMOVED, left=item, right=None)
        for path, item in left_files.items()
        if path not in right_files
    ]


def _changed_changes(
    left_files: dict[str, SnapshotFile], right_files: dict[str, SnapshotFile]
) -> list[SnapshotChange]:
    return [
        SnapshotChange(
            path=path,
            kind=SnapshotChangeKind.CHANGED,
            left=item,
            right=right_files[path],
        )
        for path, item in left_files.items()
        if path in right_files and right_files[path].sha256 != item.sha256
    ]


def _file_sha256(path: Path) -> str:
    """分块摘要（不把整个文件读进内存）。"""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_DIGEST_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()
