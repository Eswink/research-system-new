"""FileSnapshotReader：内容寻址快照目录的只读枚举（PLAN-20260915-058 WP-B）。

目录布局与 `FileWorkspaceBackend` 一致：`<root>/.snapshots/<digest 的 hex>/`。
本类只读该目录，**不**触碰 `<root>/<workspace_id>` 工作区目录，也不获取 lease。

安全边界（控制面首次接触宿主文件系统，逐条收窄）：

- 只接受 `sha256:<64 hex>` 形式的 digest；路径不能由调用方提供，因此无路径穿越面；
- 解析后的目录必须仍在 `<root>/.snapshots` 之内（包含性检查）；
- 快照目录内出现 symlink 一律拒绝（`POLICY_DENIED`），不跟随链接读取宿主文件；
- 未保留的 digest → `InvalidInputError`（控制面 404），不返回空树。
"""

from __future__ import annotations

import re
from pathlib import Path

from packages.application.ports.errors import InvalidInputError, PermanentPortError
from packages.application.workspace.snapshot_tree import SnapshotTree, snapshot_tree
from packages.domain.enums import FailureCategory

_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class FileSnapshotReader:
    """把 `<root>/.snapshots/<hex>` 解析成只读文件清单。"""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root).resolve()
        self._snapshots = self._root / ".snapshots"

    def retained_digests(self) -> frozenset[str]:
        if not self._snapshots.is_dir():
            return frozenset()
        digests = set()
        for child in self._snapshots.iterdir():
            if child.is_symlink() or not child.is_dir():
                continue
            digest = f"sha256:{child.name}"
            if _DIGEST_RE.fullmatch(digest) is not None:
                digests.add(digest)
        return frozenset(digests)

    def snapshot_files(self, digest: str) -> SnapshotTree:
        directory = self._resolve(digest)
        self._reject_symlinks(directory)
        return snapshot_tree(directory)

    def _resolve(self, digest: str) -> Path:
        if _DIGEST_RE.fullmatch(digest) is None:
            raise InvalidInputError(f"unknown snapshot digest: {digest!r}")
        directory = (self._snapshots / digest.split(":", 1)[1]).resolve()
        if not directory.is_relative_to(self._snapshots.resolve()):
            raise InvalidInputError(f"snapshot digest escapes root: {digest!r}")
        if not directory.is_dir():
            raise InvalidInputError(f"unknown snapshot digest: {digest}")
        return directory

    def _reject_symlinks(self, directory: Path) -> None:
        for path in directory.rglob("*"):
            if path.is_symlink():
                raise PermanentPortError(
                    f"symlink in snapshot is not permitted: {path.name!r}",
                    failure_category=FailureCategory.POLICY_DENIED,
                )
