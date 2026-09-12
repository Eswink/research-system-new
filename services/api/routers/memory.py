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
- capability policy 面（policy.yaml `_CAPABILITY_SCOPE` 镜像契约）当前不
  含 memory.write；把 memory.write 纳入 capability 注册表属 policy 面扩展
  （follow-up），此处 policy 槽位显式 None，写入门槛由 provenance 白名单
  （ledger.has_source）+ PROJECT/ORGANIZATION tier 的 curator 门承担。
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from packages.application.memory.gate import MemoryGateDeps, commit_memory
from packages.application.memory.lifecycle import MemoryLifecycleDeps, delete_memory
from packages.application.ports import InvalidInputError
from packages.domain.core import ID
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryRecord, MemoryWriteProposal
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.memory import (
    MemoryCommittedDto,
    MemoryListViewDto,
    MemoryProposalDto,
    MemoryRecordDto,
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


def _record_dto(record: MemoryRecord) -> MemoryRecordDto:
    return MemoryRecordDto(
        id=record.id,
        tier=_enum_value(record.tier),
        kind=_enum_value(record.kind),
        content=record.content,
        provenance=record.provenance,
        confidence=record.confidence,
        valid_from=record.valid_from.value.isoformat() if record.valid_from else None,
        review_after=record.review_after.value.isoformat() if record.review_after else None,
        expires_at=record.expires_at.value.isoformat() if record.expires_at else None,
        supersedes=list(record.supersedes),
        active=record.active,
    )


@router.get("/projects/{project_id}/memory", response_model=MemoryListViewDto)
async def list_project_memory(project_id: str, request: Request) -> MemoryListViewDto:
    del project_id  # 单项目上下文；scope_note 明示无 principal 过滤
    deps: ApiDeps = get_deps(request)
    store = _store_of(deps)
    records = store.query()  # type: ignore[attr-defined]
    return MemoryListViewDto(
        records=[_record_dto(record) for record in records], scope_note=SCOPE_NOTE
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
    """门依赖：policy 槽位显式 None（见模块 docstring），写入门槛由
    provenance 白名单（ledger 验证）+ tier/curator 门承担。"""
    return MemoryGateDeps(
        store=_store_of(deps),  # type: ignore[arg-type]
        policy=None,
        ledger=deps.ledger,
        publisher=deps.events,
    )


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
