"""Artifact 控制面只读路由（WP-C）：run 列表 / 元数据 / 内容下载。

诚实边界：store 未配置 → 503（不伪装空列表）；未知 id → 404；
tombstone/缺 blob → 410（不 200 空字节）；超大内容 → 413（store 为
全内存 get，上限是保护而非分页）。媒体类型白名单之外一律
octet-stream + attachment（防内联执行）。
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request, Response

from packages.application.artifacts.diff import (
    ArtifactDiff,
    DiffSide,
    DiffUnavailable,
    diff_artifacts,
)
from packages.application.ports.errors import InvalidInputError
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.artifacts import (
    ArtifactDiffDto,
    ArtifactDiffLineDto,
    ArtifactDiffStatsDto,
    ArtifactDto,
)
from services.api.errors import ApiError
from services.api.run_access import get_run_or_error

router = APIRouter(tags=["artifacts"])

MAX_CONTENT_BYTES = 10 * 1024 * 1024
# diff 上限更小：两侧都要建行索引（超限时直接给 unavailable，不读内容）。
MAX_DIFF_BYTES = 2 * 1024 * 1024
# 内联预览白名单（窄集：text/html|xml|javascript 等可执行/可引用类型一律下载）
_INLINE_MEDIA = (
    "text/plain",
    "text/csv",
    "text/markdown",
    "application/json",
    "image/png",
    "image/jpeg",
)


def _store(deps: ApiDeps) -> Any:
    if deps.artifacts is None:
        raise ApiError(503, "Artifact Store Unavailable", "artifact store not configured")
    return deps.artifacts


def _artifact_dto(artifact: Any, verified: bool | None = None) -> ArtifactDto:
    policy = artifact.retention_policy
    return ArtifactDto(
        id=artifact.id,
        digest=str(artifact.digest),
        size_bytes=artifact.size_bytes,
        media_type=artifact.media_type,
        state=str(artifact.state.value if hasattr(artifact.state, "value") else artifact.state),
        created_by=artifact.created_by,
        source_refs=list(artifact.source_refs),
        classification=artifact.classification,
        retention_policy=policy.to_str() if policy is not None else None,
        created_at=str(artifact.created_at) if artifact.created_at is not None else None,
        verified=verified,
    )


def _run_artifact_ids(deps: ApiDeps, store: Any, run_id: str) -> list[str]:
    """run 作用域 artifact：evidence ledger 引用 ∪ source_refs/id 任务约定。"""
    ids: set[str] = set()
    for evidence in _run_evidence(deps, run_id):
        if evidence.artifact_id:
            ids.add(evidence.artifact_id)
    task_ids = _run_task_ids(deps, run_id)
    for artifact in store.list_refs():
        refs = set(artifact.source_refs)
        if any(ref in {f"task:{t}" for t in task_ids} for ref in refs) or _task_prefixed(
            artifact.id, task_ids
        ):
            ids.add(artifact.id)
    return sorted(ids)


def _run_evidence(deps: ApiDeps, run_id: str) -> list[Any]:
    if deps.ledger is None:
        return []
    found: list[Any] = []
    seen: set[str] = set()
    for claim in deps.ledger.claims():
        for relation in deps.ledger.relations_for_claim(claim.id):
            if relation.evidence_id in seen:
                continue
            seen.add(relation.evidence_id)
            try:
                evidence = deps.ledger.get_evidence(relation.evidence_id)
            except Exception:  # noqa: BLE001 - 引用可能已删除
                continue
            if evidence.run_id == run_id:
                found.append(evidence)
    return found


def _run_task_ids(deps: ApiDeps, run_id: str) -> set[str]:
    if deps.projection is None:
        return set()
    return {task.id.value for task, _contract in deps.projection.list_tasks(run_id)}


def _task_prefixed(artifact_id: str, task_ids: set[str]) -> bool:
    prefix = artifact_id.split(":", 1)[0]
    return prefix in task_ids


@router.get("/runs/{run_id}/artifacts", response_model=list[ArtifactDto])
async def list_run_artifacts(run_id: str, request: Request) -> list[ArtifactDto]:
    """Run 产物列表（存在 run 才查询；store 缺失 503）。"""
    deps: ApiDeps = get_deps(request)
    get_run_or_error(deps, run_id)
    store = _store(deps)
    result: list[ArtifactDto] = []
    for artifact_id in _run_artifact_ids(deps, store, run_id):
        meta = store.meta(artifact_id)
        if meta is not None:
            result.append(_artifact_dto(meta))
    return result


@router.get("/artifacts/{artifact_id}", response_model=ArtifactDto)
async def get_artifact(artifact_id: str, request: Request) -> ArtifactDto:
    """单 artifact 元数据（含内容级 digest 校验结果）。"""
    deps: ApiDeps = get_deps(request)
    store = _store(deps)
    meta = store.meta(artifact_id)
    if meta is None:
        raise ApiError(404, "Artifact Not Found", f"unknown artifact id: {artifact_id}")
    verified = _safe_verify(store, artifact_id)
    return _artifact_dto(meta, verified=verified)


def _safe_verify(store: Any, artifact_id: str) -> bool | None:
    """DELETED_TOMBSTONE 上 verify 会抛错：以 None 表示不可校验状态。"""
    try:
        return bool(store.verify(artifact_id))
    except Exception:  # noqa: BLE001 - 已删除/缺 blob 均归入不可校验
        return None


def _content_headers(artifact: Any) -> tuple[str, dict[str, str]]:
    inline = artifact.media_type.startswith(_INLINE_MEDIA)
    media = artifact.media_type if inline else "application/octet-stream"
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in artifact.id)[-120:]
    disposition = "inline" if inline else "attachment"
    headers = {
        "Content-Disposition": f'{disposition}; filename="{safe_name}"',
        "X-Content-Type-Options": "nosniff",
        "ETag": f'"{artifact.digest}"',
    }
    return media, headers


@router.get("/artifacts/{artifact_id}/content")
async def get_artifact_content(artifact_id: str, request: Request) -> Response:
    """内容下载/白名单内联预览（tombstone/缺 blob → 410；超限 → 413）。"""
    deps: ApiDeps = get_deps(request)
    store = _store(deps)
    meta = store.meta(artifact_id)
    if meta is None:
        raise ApiError(404, "Artifact Not Found", f"unknown artifact id: {artifact_id}")
    if str(getattr(meta.state, "value", meta.state)) == "DELETED_TOMBSTONE":
        raise ApiError(410, "Artifact Deleted", f"artifact deleted: {artifact_id}")
    if meta.size_bytes > MAX_CONTENT_BYTES:
        raise ApiError(
            413,
            "Artifact Too Large",
            f"artifact exceeds {MAX_CONTENT_BYTES} byte inline limit",
        )
    try:
        content = store.get(artifact_id)
    except InvalidInputError as exc:
        raise ApiError(410, "Artifact Unavailable", str(exc)) from exc
    except FileNotFoundError as exc:
        raise ApiError(410, "Artifact Blob Missing", "content blob is unavailable") from exc
    media, headers = _content_headers(meta)
    return Response(content=content, media_type=media, headers=headers)


@router.get("/artifacts/{left_id}/diff/{right_id}", response_model=ArtifactDiffDto)
async def diff_artifacts_route(left_id: str, right_id: str, request: Request) -> ArtifactDiffDto:
    """两制品内容行级 diff（PLAN-047；只读派生，不落库）。

    404（任一侧未知 id）/ 503（store 未配置）/ 410（tombstone 或 blob 缺失）；
    二进制或超限**不是错误**而是 `available=false` + reason —— 与"无差异"严格区分。
    """
    deps: ApiDeps = get_deps(request)
    store = _store(deps)
    left = _diff_meta(store, left_id)
    right = _diff_meta(store, right_id)
    too_large = max(left.size_bytes, right.size_bytes) > MAX_DIFF_BYTES
    view = (
        _unavailable_diff(left.digest, right.digest)
        if too_large
        else diff_artifacts(_diff_side(store, left, left_id), _diff_side(store, right, right_id))
    )
    return _diff_dto(view)


def _diff_meta(store: Any, artifact_id: str) -> Any:
    meta = store.meta(artifact_id)
    if meta is None:
        raise ApiError(404, "Artifact Not Found", f"unknown artifact id: {artifact_id}")
    if str(getattr(meta.state, "value", meta.state)) == "DELETED_TOMBSTONE":
        raise ApiError(410, "Artifact Deleted", f"artifact deleted: {artifact_id}")
    return meta


def _diff_side(store: Any, meta: Any, artifact_id: str) -> DiffSide:
    return DiffSide(digest=str(meta.digest), content=_blob(store, artifact_id), label=artifact_id)


def _blob(store: Any, artifact_id: str) -> bytes:
    try:
        return bytes(store.get(artifact_id))
    except InvalidInputError as exc:
        raise ApiError(410, "Artifact Unavailable", str(exc)) from exc
    except FileNotFoundError as exc:
        raise ApiError(410, "Artifact Blob Missing", "content blob is unavailable") from exc


def _unavailable_diff(left_digest: str, right_digest: str) -> ArtifactDiff:
    """超限时不读取内容：直接给 unavailable 结果（不把超大内容拉进内存）。"""
    return ArtifactDiff(
        left_digest=left_digest,
        right_digest=right_digest,
        available=False,
        identical=False,
        reason=DiffUnavailable.TOO_LARGE,
    )


def _diff_dto(view: ArtifactDiff) -> ArtifactDiffDto:
    return ArtifactDiffDto(
        left_digest=view.left_digest,
        right_digest=view.right_digest,
        available=view.available,
        identical=view.identical,
        reason=view.reason.value if view.reason is not None else None,
        lines=[ArtifactDiffLineDto(kind=line.kind.value, text=line.text) for line in view.lines],
        stats=ArtifactDiffStatsDto(
            added=view.stats.added, removed=view.stats.removed, context=view.stats.context
        ),
        truncated=view.truncated,
    )
