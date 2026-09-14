"""Run deliverable 只读路由（PLAN-043 WP-A，EC-02）。

`GET /runs/{run_id}/deliverable` 读取 M12 `build_deliverable` 的 persisted
`deliverable.json` artifact（由 `persist_completion` 落盘）。非交付 run 诚实
返回 available=false，不生成空报告冒充。
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Request

from packages.application.ports.errors import InvalidInputError
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.inspection import DeliverableDto
from services.api.errors import ApiError
from services.api.run_access import get_run_or_error

router = APIRouter(tags=["inspection"])

_DELIVERABLE_ARTIFACT = "deliverable.json"


def _artifact_ref(run_id: str) -> str:
    return f"{run_id}:{_DELIVERABLE_ARTIFACT}"


def _load(deps: ApiDeps, run_id: str) -> tuple[dict[str, object] | None, str | None, str | None]:
    """读取 persisted deliverable → (deliverable, artifact_id, digest)。

    未产出 / 损坏 JSON 均返回 deliverable=None（调用方据 artifact_id 区分原因）。
    """
    store = deps.artifacts
    if store is None:
        return None, None, None
    artifact_id = _artifact_ref(run_id)
    meta = store.meta(artifact_id)
    if meta is None:
        return None, None, None
    digest = str(meta.digest)
    try:
        payload = json.loads(store.get(artifact_id))
    except (ValueError, FileNotFoundError, InvalidInputError):
        return None, artifact_id, digest
    if not isinstance(payload, dict):
        return None, artifact_id, digest
    return payload, artifact_id, digest


@router.get("/runs/{run_id}/deliverable", response_model=DeliverableDto)
async def run_deliverable(run_id: str, request: Request) -> DeliverableDto:
    """Run 研究报告（M12 build_deliverable 的 persisted 产物）。

    run 未知 → 404（对齐 /usage/export）；store 缺失 → 503；run 存在但未产出
    交付物 → 200 + available=false（诚实空态）。
    """
    deps: ApiDeps = get_deps(request)
    get_run_or_error(deps, run_id)
    if deps.artifacts is None:
        raise ApiError(503, "Artifact Store Unavailable", "artifact store not configured")
    deliverable, artifact_id, digest = _load(deps, run_id)
    if deliverable is None:
        return DeliverableDto(
            run_id=run_id,
            available=False,
            reason=(
                "该 Run 尚无持久化交付物（仅完成 M12 参考链的 Run 产出 deliverable.json）"
                if artifact_id is None
                else "交付物存在但内容不可解析"
            ),
            artifact_id=artifact_id,
            artifact_digest=digest,
        )
    return DeliverableDto(
        run_id=run_id,
        available=True,
        artifact_id=artifact_id,
        artifact_digest=digest,
        deliverable=deliverable,
    )
