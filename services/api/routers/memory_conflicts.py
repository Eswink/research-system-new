"""证据矛盾的**消解路由**（GOAL-20261111-110 EC-02）。

**为什么单列**：`routers/memory.py` 已 452 行（450 行硬上限）；消解是**新的一类动作**
（仲裁 + 落账），与既有四个路由（读列表 / 时效读面 / 提案 / 删除）的读写面不同 ⇒
单列不改变任何既有语义，只把新面放在自己的模块里。

**它守的纪律**（逐条对应 GOAL 的 EC）：

1. **缺省 `REQUIRE_HUMAN`**：不声明策略 ⇒ 返回判词、**不落账**（§9 同姿态）；
2. **自动化必须显式**：`DeclaredPolicy` 需要 `strategy` + `min_confidence`；缺阈值 ⇒ 422；
3. **落账走既有用例**：`lifecycle.resolve_memory_conflict`（不新造第二套写面）；
4. **幂等由既有中间件强制**（本模块不自建第二套）。

**射程（不宣称）**：只做**单对**消解；批量闭环与前端未接（GOAL 的 `U-1` / `U-2`）。
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from packages.application.memory.arbitration import (
    NEWER_WINS,
    REQUIRE_HUMAN,
    SOURCE_TRUST_WINS,
    DeclaredPolicy,
    arbitrate,
)
from packages.application.memory.lifecycle import (
    MemoryLifecycleDeps,
    resolve_memory_conflict,
)
from packages.application.ports import InvalidInputError
from packages.domain.core import Timestamp
from packages.domain.memory import MemoryRecord
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.memory import (
    MemoryConflictResolveDto,
    MemoryConflictResolveViewDto,
    MemoryConflictVerdictDto,
)
from services.api.errors import ApiError
from services.api.routers.memory import _record_dto, _store_of

router = APIRouter(tags=["memory"])


def _memory_or_404(store: Any, memory_id: str) -> MemoryRecord:
    """取一条记录；未知 id ⇒ 404 点名（与既有删除路由同形态）。"""
    try:
        return store.get(memory_id)  # type: ignore[no-any-return]
    except InvalidInputError as exc:
        raise ApiError(404, "Memory Not Found", f"unknown memory id: {memory_id}") from exc


def _declared_policy(payload: MemoryConflictResolveDto) -> DeclaredPolicy | None:
    """请求体 → 显式策略（`None` = 缺省 REQUIRE_HUMAN / 人来裁决两种形态）。"""
    if payload.strategy is None or payload.strategy == REQUIRE_HUMAN:
        return None
    if payload.strategy not in {NEWER_WINS, SOURCE_TRUST_WINS}:
        raise ApiError(
            422,
            "Unknown Arbitration Strategy",
            f"strategy must be one of "
            f"{sorted({NEWER_WINS, SOURCE_TRUST_WINS, REQUIRE_HUMAN})}, "
            f"got {payload.strategy!r}",
        )
    if payload.min_confidence is None:
        raise ApiError(
            422,
            "Arbitration Threshold Required",
            "declaring an automatic strategy requires min_confidence "
            "(an unthresholded who-is-right is not declarable)",
        )
    return DeclaredPolicy(strategy=payload.strategy, min_confidence=payload.min_confidence)


def _resolution_direction(left: MemoryRecord, right: MemoryRecord) -> tuple[str, str]:
    """落账方向：**谁声明了冲突就记在谁身上**（请求方向只是入口，不是记账键）。

    非声明的冲突对 ⇒ 422 点名（先于仲裁——「不是一对」与「裁不出来」是两件事）。
    """
    if right.id in left.contradictions:
        return left.id, right.id
    if left.id in right.contradictions:
        return right.id, left.id
    raise ApiError(
        422,
        "Not A Declared Conflict Pair",
        f"neither {left.id!r} nor {right.id!r} declares the other as a contradiction",
    )


def _verdict_dto(verdict: Any) -> MemoryConflictVerdictDto:
    return MemoryConflictVerdictDto(
        outcome=verdict.outcome,
        winner_id=verdict.winner_id,
        basis=verdict.basis,
        missing=list(verdict.missing),
    )


@router.post(
    "/memory/{memory_id}/conflicts/{other_id}/resolve",
    response_model=MemoryConflictResolveViewDto,
)
async def resolve_memory_conflict_route(
    memory_id: str,
    other_id: str,
    request: Request,
    payload: MemoryConflictResolveDto | None = None,
) -> MemoryConflictResolveViewDto:
    """**消解一条冲突**：仲裁 → 可判依据 → （依据成立时）落账。

    缺省（无请求体 / 无 `strategy`）⇒ `REQUIRE_HUMAN` 判词返回 200，**不**落账。
    声明自动策略且依据齐备 ⇒ 经 `lifecycle.resolve_memory_conflict` 落账
    （`resolved_by="arbitration:<strategy>"`）。声明 `REQUIRE_HUMAN` 且带 `resolved_by`
    ⇒ **人来裁决**落账（`resolved_by` 逐字入账）。
    """
    deps: ApiDeps = get_deps(request)
    store = _store_of(deps)
    body = payload or MemoryConflictResolveDto()
    left = _memory_or_404(store, memory_id)
    right = _memory_or_404(store, other_id)
    holder, other = _resolution_direction(left, right)
    verdict = arbitrate(
        left,
        right,
        policy=_declared_policy(body),
        trust_labels=dict(body.trust_labels) if body.trust_labels else None,
    )
    if verdict.outcome == REQUIRE_HUMAN and not body.resolved_by:
        return MemoryConflictResolveViewDto(
            verdict=_verdict_dto(verdict),
            resolution_recorded=False,
        )
    attributed = body.resolved_by if body.resolved_by else f"arbitration:{verdict.outcome}"
    updated = resolve_memory_conflict(
        MemoryLifecycleDeps(store=store, publisher=deps.events),  # type: ignore[arg-type]
        holder,
        other,
        resolved_by=attributed,
        resolved_at=Timestamp.now(),
    )
    return MemoryConflictResolveViewDto(
        verdict=_verdict_dto(verdict),
        resolution_recorded=True,
        record=_record_dto(updated),
    )


__all__ = ["router"]
