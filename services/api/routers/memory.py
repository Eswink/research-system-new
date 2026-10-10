"""Memory 控制面路由（PLAN-20260910-037 WP-F）。

写路径完整执行 AGENTS.md §8 门链（schema → provenance → contradiction →
policy → curator gate → sanitize-before-commit → commit + 事件），复用
packages.application.memory 用例，不另建第二套 gate。

诚实边界：
- store 未配置 → 503（不伪装空列表）；
- 门链拒绝 → 422（stage + reasons 可分类）；
- 域内无持久化 pending 提案，故不提供两阶段 decide（curator_approved 为
  提案参数）；
- 无 principal/多项目边界（M18 deferred）→ 列表带 scope_note，不假称
  project 过滤；
- policy 槽位注入真实求值器（PLAN-20260914-049）：policy.yaml 的
  `memory.write` 规则按 tier 生效（deny → 422 policy 阶段；require_approval
  仍需 curator 输入）；policy 文件不可解析时 evaluator 为 None，门链按既有
  行为继续（不伪造默认策略），provenance 白名单（ledger.has_source）+
  PROJECT/ORGANIZATION tier 的 curator 门始终兜底。
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Request

from packages.application.memory.gate import MemoryGateDeps, commit_memory
from packages.application.memory.lifecycle import MemoryLifecycleDeps, delete_memory
from packages.application.memory.validity import validity_at
from packages.application.ports import InvalidInputError
from packages.domain.core import ID, Timestamp
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryRecord, MemoryWriteProposal
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.memory import (
    MemoryCommittedDto,
    MemoryFilteredListViewDto,
    MemoryListViewDto,
    MemoryProposalDto,
    MemoryRecordDto,
    MemoryValidityDto,
    MemoryValidityViewDto,
)
from services.api.errors import ApiError

router = APIRouter(tags=["memory"])

SCOPE_NOTE = (
    "控制面无 principal/多项目授权（M18 deferred）；此处为单项目上下文全量 "
    "Memory 记录（含 active=False tombstone），不假称 project 过滤。"
)


def _store_of(deps: ApiDeps) -> object:
    if deps.memory is None:
        raise ApiError(
            503,
            "Memory Store Unavailable",
            "memory store not configured",
        )
    return deps.memory


def _enum_value(value: object) -> str:
    return getattr(value, "value", str(value))


def _record_dto(record: MemoryRecord, *, now: Timestamp | None = None) -> MemoryRecordDto:
    """记录 DTO。**只在给了时点时**填 `validity`（不给 ⇒ `None` = 未判定，不猜）。"""
    validity = validity_at(record, now) if now is not None else None
    return MemoryRecordDto(
        id=record.id,
        tier=_enum_value(record.tier),
        kind=_enum_value(record.kind),
        content=record.content,
        provenance=record.provenance,
        confidence=record.confidence,
        scope=record.scope,
        validity=validity.value if validity is not None else None,
        valid_from=record.valid_from.value.isoformat() if record.valid_from else None,
        review_after=record.review_after.value.isoformat() if record.review_after else None,
        expires_at=record.expires_at.value.isoformat() if record.expires_at else None,
        supersedes=list(record.supersedes),
        active=record.active,
    )


@router.get(
    "/projects/{project_id}/memory",
    # 两个形态的**并集**：`MemoryFilteredListViewDto` 继承缺省形态并追加两键。
    response_model=MemoryListViewDto | MemoryFilteredListViewDto,
)
async def list_project_memory(
    project_id: str, request: Request, scope: str | None = None
) -> MemoryListViewDto:
    """项目内的记忆清单（**可选**按 `scope` 筛；缺省不筛 ⇒ 既有行为逐字不变）。

    GOAL-20261010-049 EC-03：`scope` 是**声明的范围**（不是 ACL）—— `scope_note` 照旧
    明示「无 principal/多项目授权」；带了 `scope` 时另报 `filtered_out`（**不静默丢**）。
    """
    del project_id  # 单项目上下文；scope_note 明示无 principal 过滤
    deps: ApiDeps = get_deps(request)
    store = _store_of(deps)
    records = store.query(scope=scope)  # type: ignore[attr-defined]
    # 两个形态各自**显式**声明自己的键（不给路由开 `response_model_exclude_none`：那种开关
    # 会连**嵌套模型**一起递归应用，把别的读面上**有意义**的 `null` 抹掉 —— 实测过）。
    if scope is None:
        return MemoryListViewDto(
            records=[_record_dto(record) for record in records], scope_note=SCOPE_NOTE
        )
    return MemoryFilteredListViewDto(
        records=[_record_dto(record) for record in records],
        scope_note=SCOPE_NOTE,
        scope=scope,
        filtered_out=len(store.query()) - len(records),  # type: ignore[attr-defined]
    )


def _proposal(payload: MemoryProposalDto) -> MemoryWriteProposal:
    try:
        tier = MemoryTier(payload.tier)
        kind = MemoryType(payload.kind)
    except ValueError as exc:
        raise ApiError(422, "Invalid Memory Tier/Kind", str(exc)) from exc
    return MemoryWriteProposal(
        id=ID.generate().value,
        tier=tier,
        kind=kind,
        content=payload.content,
        provenance=payload.provenance,
        confidence=payload.confidence,
        proposed_by=payload.proposed_by,
        supersedes=list(payload.supersedes),
    )


def _gate_deps(deps: ApiDeps) -> MemoryGateDeps:
    """门依赖：policy 面注入 composition 装配的求值器（PLAN-20260914-049）；
    policy.yaml 不可用时为 None，此时门槛由 provenance 白名单（ledger 验证）
    + tier/curator 门承担（与接线前一致，不伪造默认策略）。"""
    return MemoryGateDeps(
        store=_store_of(deps),  # type: ignore[arg-type]
        policy=deps.policy_evaluator,
        ledger=deps.ledger,
        publisher=deps.events,
    )


@router.get("/projects/{project_id}/memory/validity", response_model=MemoryValidityViewDto)
async def memory_validity(project_id: str, at: str, request: Request) -> MemoryValidityViewDto:
    """**按显式时点**给出每条记忆的时效（GOAL-20261008-039 EC-04）。

    **为什么是 GET**：判定只依赖（canonical 状态 × 显式时点）—— 是**读面**（与既有
    `GET /projects/{id}/memory` 同一族，读面不认证）；**没有业务写入** ⇒ 不该挂进写面。

    时点由调用方给（`?at=`）⇒ 判定可复现（**不读挂钟**）。三态见 `validity_at`：
    `EXPIRED` / `REVIEW_DUE` / `None`（未到期**或未声明** —— 不猜）。
    """
    del project_id  # 单项目上下文（与既有列表读面同一条 scope_note 边界）
    deps: ApiDeps = get_deps(request)
    store = _store_of(deps)
    try:
        moment = Timestamp(datetime.fromisoformat(at))
    except ValueError as exc:
        raise ApiError(422, "Invalid Timestamp", str(exc)) from exc
    records = store.query()  # type: ignore[attr-defined]
    rows: list[MemoryValidityDto] = []
    for record in records:
        state = validity_at(record, moment)
        rows.append(
            MemoryValidityDto(
                id=record.id,
                scope=record.scope,
                review_after=record.review_after.value.isoformat() if record.review_after else None,
                expires_at=record.expires_at.value.isoformat() if record.expires_at else None,
                validity=state.value if state is not None else None,
            )
        )
    return MemoryValidityViewDto(at=moment.value.isoformat(), records=rows, scope_note=SCOPE_NOTE)


@router.post("/memory/proposals", response_model=MemoryCommittedDto, status_code=201)
async def propose_memory(payload: MemoryProposalDto, request: Request) -> MemoryCommittedDto:
    """提案即走完整 §8 门链提交；拒绝以 stage+reasons 分类为 422。"""
    deps: ApiDeps = get_deps(request)
    result = commit_memory(
        _proposal(payload),
        _gate_deps(deps),
        curator_approved=payload.curator_approved,
    )
    record = result.record
    if not result.accepted or record is None:
        raise ApiError(
            422,
            f"Memory Proposal {result.stage}",
            "; ".join(result.reasons) or "rejected by memory gate",
        )
    return MemoryCommittedDto(record=_record_dto(record), decision=result.decision.value)


@router.delete("/memory/{memory_id}", status_code=204)
async def remove_memory(memory_id: str, request: Request) -> None:
    """物理删除 canonical 记录（lifecycle 用例：索引同步 + MEMORY_DELETED 事件）。"""
    deps: ApiDeps = get_deps(request)
    store = _store_of(deps)
    try:
        store.get(memory_id)  # type: ignore[attr-defined]
    except InvalidInputError as exc:
        raise ApiError(404, "Memory Not Found", f"unknown memory id: {memory_id}") from exc
    delete_memory(
        MemoryLifecycleDeps(store=store, publisher=deps.events),  # type: ignore[arg-type]
        memory_id,
    )
