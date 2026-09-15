"""FileWorkspaceBackend：WorkspaceBackend Port 的真实文件系统实现（M9）。"""

from adapters.workspace.file_backend import (
    FileWorkspaceBackend,
    workspace_tree_digest,
)
from adapters.workspace.snapshot_reader import FileSnapshotReader

__all__ = [
    "FileSnapshotReader",
    "FileWorkspaceBackend",
    "workspace_tree_digest",
]
