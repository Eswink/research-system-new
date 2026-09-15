"""工作区快照只读路由（PLAN-20260915-058 WP-C）。

只按内容寻址 digest 暴露保留中的快照；run 侧只报告"记录过哪些 digest"。

诚实边界：

- 未配置快照根（`RESEARCHOS_WORKSPACE_SNAPSHOT_ROOT`）→ 503 + 原因，不返回空树；
- digest 非法或未保留 → 404（`NOT_RETAINED` 语义），不用当前工作区内容冒充快照；
- 快照目录内出现 symlink → 403（存储被污染，不跟随链接读宿主文件）；
- 文件级 diff 只比元数据；内容行级 diff 在制品侧 `/artifacts/{a}/diff/{b}`。
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from packages.application.ports.errors import InvalidInputError, PermanentPortError
from packages.application.ports.workspace_snapshot import WorkspaceSnapshotReader
from packages.application.workspace.snapshot_tree import SnapshotTree, diff_snapshot_trees
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.workspace_snapshots import (
    RunWorkspaceSnapshotsDto,
    WorkspaceSnapshotCapabilityDto,
    WorkspaceSnapshotDiffDto,
    WorkspaceSnapshotTreeDto,
)
from services.api.errors import ApiError
from services.api.mappers.workspace_snapshots import (
    capability_dto,
    diff_dto,
    run_snapshots_dto,
    tree_dto,
)
from services.api.run_access import get_run_or_error

router = APIRouter(tags=["workspace"])


def _reader(deps: ApiDeps) -> WorkspaceSnapshotReader:
    if deps.workspace_snapshots is None:
        raise ApiError(
            503,
            "Workspace Snapshot Store Unavailable",
            "no workspace snapshot root configured (RESEARCHOS_WORKSPACE_SNAPSHOT_ROOT)",
        )
    return deps.workspace_snapshots


@router.get("/workspace-snapshots", response_model=WorkspaceSnapshotCapabilityDto)
async def workspace_snapshot_capability(request: Request) -> WorkspaceSnapshotCapabilityDto:
    """快照读取能力（未配置时 configured=False + 原因，不伪装计数）。"""
    deps: ApiDeps = get_deps(request)
    return capability_dto(deps.workspace_snapshots)


@router.get("/runs/{run_id}/workspace-snapshots", response_model=RunWorkspaceSnapshotsDto)
async def run_workspace_snapshots(run_id: str, request: Request) -> RunWorkspaceSnapshotsDto:
    """run 记录过的快照 digest 与保留状态（不推断 run→工作区绑定）。"""
    deps: ApiDeps = get_deps(request)
    get_run_or_error(deps, run_id)
    if deps.ledger is None:
        raise ApiError(503, "Evidence Ledger Unavailable", "evidence ledger not configured")
    return run_snapshots_dto(deps, deps.workspace_snapshots, run_id)


@router.get("/workspace-snapshots/{digest}/files", response_model=WorkspaceSnapshotTreeDto)
async def workspace_snapshot_files(digest: str, request: Request) -> WorkspaceSnapshotTreeDto:
    """某个保留中快照的文件清单（路径/大小/sha256）。"""
    reader = _reader(get_deps(request))
    return tree_dto(digest, _snapshot_files(reader, digest))


@router.get(
    "/workspace-snapshots/{left}/diff/{right}",
    response_model=WorkspaceSnapshotDiffDto,
)
async def workspace_snapshot_diff(
    left: str, right: str, request: Request
) -> WorkspaceSnapshotDiffDto:
    """两个保留中快照的文件级 diff（新增/删除/内容变化）。"""
    reader = _reader(get_deps(request))
    diff = diff_snapshot_trees(
        _snapshot_files(reader, left),
        _snapshot_files(reader, right),
        left_digest=left,
        right_digest=right,
    )
    return diff_dto(diff)


def _snapshot_files(reader: WorkspaceSnapshotReader, digest: str) -> SnapshotTree:
    try:
        return reader.snapshot_files(digest)
    except InvalidInputError as exc:
        raise ApiError(404, "Snapshot Not Retained", str(exc)) from exc
    except PermanentPortError as exc:
        raise ApiError(403, "Snapshot Rejected", str(exc)) from exc
