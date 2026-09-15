"""工作区快照只读控制面 DTO（PLAN-20260915-058；无 Domain 类型泄漏）。

口径：只按内容寻址 digest 暴露**保留中**的快照；文件级 diff 只比元数据
（路径/大小/sha256），内容行级 diff 属于制品侧 `/artifacts/{a}/diff/{b}`。
"""

from __future__ import annotations

from pydantic import BaseModel

# 能力面：未配置快照根时 configured=False，原因必须随响应返回（不伪装可用）。
CAPABILITY_NOTE_CONFIGURED = (
    "snapshot store is configured; digests come from evidence/experiment records "
    "and are resolved against the content-addressed snapshot directory"
)
CAPABILITY_NOTE_UNCONFIGURED = (
    "no workspace snapshot root configured (RESEARCHOS_WORKSPACE_SNAPSHOT_ROOT); "
    "the control plane cannot enumerate workspace snapshots"
)
RUN_NOTE = (
    "these are the snapshot digests this run recorded (evidence/experiment); "
    "the control plane does not persist a run-to-workspace binding, so 'retained' "
    "only means the digest is present in the configured snapshot store"
)
DIFF_NOTE = (
    "file-level comparison only (path/size/sha256); content line diff is served "
    "by GET /artifacts/{left}/diff/{right}"
)


class WorkspaceSnapshotCapabilityDto(BaseModel):
    """快照读取能力：未配置时 configured=False + reason，不返回假计数。"""

    configured: bool
    retained_snapshots: int
    max_files_per_snapshot: int
    note: str


class WorkspaceSnapshotFileDto(BaseModel):
    path: str
    size_bytes: int
    sha256: str


class WorkspaceSnapshotTreeDto(BaseModel):
    digest: str
    files: list[WorkspaceSnapshotFileDto]
    file_count: int
    total_bytes: int
    truncated: bool


class WorkspaceSnapshotChangeDto(BaseModel):
    path: str
    kind: str
    left_sha256: str | None = None
    right_sha256: str | None = None
    left_size_bytes: int | None = None
    right_size_bytes: int | None = None


class WorkspaceSnapshotDiffDto(BaseModel):
    left_digest: str
    right_digest: str
    comparison: str = "WORKSPACE_SNAPSHOT_METADATA"
    identical: bool
    added: int
    removed: int
    changed: int
    unchanged: int
    changes: list[WorkspaceSnapshotChangeDto]
    truncated: bool
    note: str = DIFF_NOTE


class RunWorkspaceSnapshotDto(BaseModel):
    digest: str
    recorded_as: list[str]
    retained: bool


class RunWorkspaceSnapshotsDto(BaseModel):
    run_id: str
    snapshots: list[RunWorkspaceSnapshotDto]
    note: str = RUN_NOTE
