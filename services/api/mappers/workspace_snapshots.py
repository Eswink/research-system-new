"""工作区快照只读投影（PLAN-20260915-058 WP-C）。

从 evidence 行收集 run 记录过的快照 digest，并把读者能解析的部分投影成
文件树 / 文件级 diff。run→工作区的绑定不在持久面内（见 DTO 的 `note`），
因此这里**只**回答"记录过哪些 digest、其中哪些仍保留"。
"""

from __future__ import annotations

from packages.application.ports.workspace_snapshot import WorkspaceSnapshotReader
from packages.application.workspace.snapshot_tree import (
    MAX_SNAPSHOT_FILES,
    SnapshotChange,
    SnapshotDiff,
    SnapshotTree,
)
from services.api.composition import ApiDeps
from services.api.dto.workspace_snapshots import (
    CAPABILITY_NOTE_CONFIGURED,
    CAPABILITY_NOTE_UNCONFIGURED,
    RunWorkspaceSnapshotDto,
    RunWorkspaceSnapshotsDto,
    WorkspaceSnapshotCapabilityDto,
    WorkspaceSnapshotChangeDto,
    WorkspaceSnapshotDiffDto,
    WorkspaceSnapshotFileDto,
    WorkspaceSnapshotTreeDto,
)
from services.api.run_evidence import evidence_of_run


def capability_dto(reader: WorkspaceSnapshotReader | None) -> WorkspaceSnapshotCapabilityDto:
    configured = reader is not None
    return WorkspaceSnapshotCapabilityDto(
        configured=configured,
        retained_snapshots=len(reader.retained_digests()) if reader is not None else 0,
        max_files_per_snapshot=MAX_SNAPSHOT_FILES,
        note=CAPABILITY_NOTE_CONFIGURED if configured else CAPABILITY_NOTE_UNCONFIGURED,
    )


def tree_dto(digest: str, tree: SnapshotTree) -> WorkspaceSnapshotTreeDto:
    files = [
        WorkspaceSnapshotFileDto(path=item.path, size_bytes=item.size_bytes, sha256=item.sha256)
        for item in tree.files
    ]
    return WorkspaceSnapshotTreeDto(
        digest=digest,
        files=files,
        file_count=len(files),
        total_bytes=sum(item.size_bytes for item in files),
        truncated=tree.truncated,
    )


def diff_dto(diff: SnapshotDiff) -> WorkspaceSnapshotDiffDto:
    return WorkspaceSnapshotDiffDto(
        left_digest=diff.left_digest,
        right_digest=diff.right_digest,
        identical=diff.identical,
        added=diff.added,
        removed=diff.removed,
        changed=diff.changed,
        unchanged=diff.unchanged,
        changes=[_change_dto(item) for item in diff.changes],
        truncated=diff.truncated,
    )


def run_snapshots_dto(
    deps: ApiDeps, reader: WorkspaceSnapshotReader | None, run_id: str
) -> RunWorkspaceSnapshotsDto:
    recorded = _recorded_digests(deps, run_id)
    retained = reader.retained_digests() if reader is not None else frozenset()
    return RunWorkspaceSnapshotsDto(
        run_id=run_id,
        snapshots=[
            RunWorkspaceSnapshotDto(
                digest=digest,
                recorded_as=sorted(sources),
                retained=digest in retained,
            )
            for digest, sources in sorted(recorded.items())
        ],
    )


def _change_dto(change: SnapshotChange) -> WorkspaceSnapshotChangeDto:
    return WorkspaceSnapshotChangeDto(
        path=change.path,
        kind=str(change.kind),
        left_sha256=change.left.sha256 if change.left is not None else None,
        right_sha256=change.right.sha256 if change.right is not None else None,
        left_size_bytes=change.left.size_bytes if change.left is not None else None,
        right_size_bytes=change.right.size_bytes if change.right is not None else None,
    )


def _recorded_digests(deps: ApiDeps, run_id: str) -> dict[str, set[str]]:
    """run 记录过的快照 digest → 来源标签（同一 digest 可能既是 before 又是 after）。"""
    recorded: dict[str, set[str]] = {}
    if deps.ledger is None:
        return recorded
    for evidence in evidence_of_run(deps.ledger, run_id):
        for digest, label in (
            (evidence.workspace_snapshot_before, "EVIDENCE_BEFORE"),
            (evidence.workspace_snapshot_after, "EVIDENCE_AFTER"),
        ):
            if digest:
                recorded.setdefault(digest, set()).add(label)
    return recorded
