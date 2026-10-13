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

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request

# GOAL-20261011-052 EC-03：共用判定取自**应用层**（`.importlinter.api` 的契约禁止
# `services.api.routers` import 具体适配器 ⇒ 同源判定必须落在应用层，两处都从那里取）。
from packages.application.memory.disposition import (
    TERMINAL_CURRENT,
    conflicted_by_index,
    dangling_reference_index,
    disposition_of,
    disposition_reason,
    resolved_pair_index,
    superseded_by_index,
    terminal_versions,
)
from packages.application.memory.gate import MemoryGateDeps, commit_memory
from packages.application.memory.lifecycle import MemoryLifecycleDeps, delete_memory
from packages.application.memory.validity import (
    ValidityState,
    conflict_timeliness_at,
    validity_at,
)
from packages.application.ports import InvalidInputError
from packages.domain.core import ID, Timestamp
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryRecord, MemoryWriteProposal
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.memory import (
    MemoryAuthoredListViewDto,
    MemoryCommittedDto,
    MemoryConflictResolutionDto,
    MemoryFilteredListViewDto,
    MemoryListViewDto,
    MemoryProposalDto,
    MemoryRecordDto,
    MemoryValidityDto,
    MemoryValidityViewDto,
)
from services.api.errors import ApiError
from services.api.memory_query_guard import reject_unknown_query_params

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


def _resolution_dtos(record: MemoryRecord) -> list[MemoryConflictResolutionDto]:
    """**冲突消解**逐对转成 DTO（GOAL-20261012-058 EC-03；与编排面**同源同值**）。

    未消解 ⇒ 空列表 ⇒ 处置仍是 `CONFLICTED`（既有行为逐字不变）。
    """
    return [
        MemoryConflictResolutionDto(
            other_id=item.other_id,
            resolved_by=item.resolved_by,
            resolved_at=item.resolved_at.value.isoformat(),
        )
        for item in record.resolutions
    ]


def _time_and_linkage_fields(
    record: MemoryRecord, validity: ValidityState | None, links: list[str]
) -> dict[str, object]:
    """**时效 + 取代**那几项（身份/内容字段就地写；判定项由 `_record_dto` 补上）。"""
    return {
        "id": record.id,
        "tier": _enum_value(record.tier),
        "kind": _enum_value(record.kind),
        "content": record.content,
        "provenance": record.provenance,
        "confidence": record.confidence,
        "scope": record.scope,
        "validity": validity.value if validity is not None else None,
        "valid_from": record.valid_from.value.isoformat() if record.valid_from else None,
        "review_after": record.review_after.value.isoformat() if record.review_after else None,
        "expires_at": record.expires_at.value.isoformat() if record.expires_at else None,
        "supersedes": list(record.supersedes),
        "active": record.active,
        "contradictions": list(record.contradictions),
        "superseded_by": links,
        # GOAL-20261012-065 EC-03：**提议者**（同一份 canonical 事实，不重写第二套判定）。
        "proposed_by": record.proposed_by,
    }


@dataclass(frozen=True, slots=True)
class _RowFacts:
    """一条记录投影所需的**同批事实**（合成一个参数对象守 `max-args` 门）。

    四件都由调用方按**同一批记录**算出来（记录自身读不出来）：反向取代 / 链终点 /
    反向冲突（已扣消解）/ 已消解的声明方。与编排面 `_RowFacts` **同形**（同源同值）。
    """

    superseded_by: list[str] = field(default_factory=list)
    terminal: dict[str, object] = field(default_factory=dict)
    conflicted_by: list[str] = field(default_factory=list)
    resolved_with: list[str] = field(default_factory=list)
    dangling_supersedes: list[str] = field(default_factory=list)
    dangling_contradictions: list[str] = field(default_factory=list)


def _record_dto(
    record: MemoryRecord, *, now: Timestamp | None = None, facts: _RowFacts | None = None
) -> MemoryRecordDto:
    """记录 DTO。**只在给了时点时**填 `validity`（不给 ⇒ `None` = 未判定，不猜）。

    GOAL-20261011-052 EC-02/EC-03：**四样与编排消费面同源** ——
    `contradictions` 取记录自身的声明；`superseded_by` 由调用方按**同一批记录**传入
    （反向链接 `superseded_by_index` 需要看见别人，单条记录读不出来）；
    `disposition` / `reason` **直接调**应用层那两个纯函数（`disposition_of` / `disposition_reason`）
    —— **不**在路由里重写第二套判定（两处各写一套 = 漂移无从发现）。

    GOAL-20261011-053 EC-02/EC-03：**链的终点**同理 —— `terminal` 也由调用方按**同一批记录**
    传入（`terminal_versions` 是应用层的纯函数，与反向链接**同一份事实的两种索引**）。
    """
    facts = facts or _RowFacts()
    validity = validity_at(record, now) if now is not None else None
    links = list(facts.superseded_by)
    chain: dict[str, object] = dict(facts.terminal)
    base = _time_and_linkage_fields(record, validity, links)
    base["superseded_by"] = links
    _decorate_conflict_and_terminal(
        base,
        record,
        _ConflictFacts(
            validity=validity,
            links=links,
            by_others=[
                item for item in facts.conflicted_by if item not in set(facts.resolved_with)
            ],
            resolved_with=list(facts.resolved_with),
            dangling_supersedes=list(facts.dangling_supersedes),
            dangling_contradictions=list(facts.dangling_contradictions),
            now=now,
            chain=chain,
        ),
    )
    # `base` 是 `dict[str, object]`（mypy 无法核对键名）⇒ 走 **pydantic 校验入口**
    # （`model_validate`）而不是 `**base` 展开 —— 后者会让 6 个键各报 arg-type。
    return MemoryRecordDto.model_validate(base)


@dataclass(frozen=True, slots=True)
class _ConflictFacts:
    """冲突面 + 链终点所需的**只读事实**（合成一个参数对象守 `max-args` 门）。

    六件都在这里（都是「同批记录算出来 / 调用方给的」）：`validity`（时效）/ `links`
    （反向取代）/ `by_others`（反向冲突）/ `resolved_with`（对端可见性）/
    `dangling_supersedes` + `dangling_contradictions`（悬空引用，两个方向）/
    `now`（时点）/ `chain`（链终点）。
    """

    validity: ValidityState | None
    links: list[str]
    by_others: list[str]
    resolved_with: list[str]
    dangling_supersedes: list[str]
    dangling_contradictions: list[str]
    now: Timestamp | None
    chain: dict[str, object]


def _decorate_conflict_and_terminal(
    base: dict[str, object], record: MemoryRecord, facts: _ConflictFacts
) -> None:
    """把**冲突面 + 链终点**的键写进 `base`（**同源**：一律直接调应用层纯函数）。

    **为什么单列**：`_record_dto` 有 50 行硬上限 —— 序 29/30 各加一个键之后一度把它顶爆
    ⇒ 逐段搬到这里（**语义一字未动**，只是换落点），并守住那道门。

    三件（都**不重写第二套判定** —— 两处各写一套 = 漂移无从发现）：

    - **消解 / 处置 / 理由**（序 17/18/19/26/30，`disposition_of` + `disposition_reason`）；
    - **冲突时效**（序 29，`conflict_timeliness_at`；不给时点 ⇒ `None` = 未判定，**不猜**）；
    - **链终点**（序 21，`chain` 由调用方按同批记录算好）。
    """
    links = facts.links
    by_others = facts.by_others
    chain_ids = facts.chain.get("terminal")
    base["conflict_resolutions"] = _resolution_dtos(record)
    base["conflicted_by"] = list(by_others)
    # GOAL-20261012-063 EC-03：**已与本记录消解的那些声明方**（对端可见性 —— 从
    # `conflicted_by` 里扣掉的那些在这里逐条点名，**不静默消失**）。
    base["resolved_with"] = list(facts.resolved_with)
    # GOAL-20261012-064 EC-03：**悬空引用**两个方向各自点名（既有键一字不动）。
    base["dangling_supersedes"] = list(facts.dangling_supersedes)
    base["dangling_contradictions"] = list(facts.dangling_contradictions)
    base["disposition"] = disposition_of(
        facts.validity,
        superseded=bool(links),
        conflicted=bool(record.unresolved_conflicts),
        conflicted_by=bool(by_others),
    )
    base["reason"] = disposition_reason(
        facts.validity, record, superseded_by=links, conflicted_by=by_others
    )
    base["conflict_timeliness"] = (
        state.value
        if facts.now is not None
        and (state := conflict_timeliness_at(record, facts.now)) is not None
        else None
    )
    base["terminal_state"] = str(facts.chain.get("state", TERMINAL_CURRENT))
    base["terminal_ids"] = (
        [str(item) for item in chain_ids] if isinstance(chain_ids, list) else [str(record.id)]
    )


@router.get(
    "/projects/{project_id}/memory",
    # **三个**形态的并集（缺省 / 按范围 / 按作者）—— 各形态都继承缺省形态并追加自己的键；
    # 少了任何一个 ⇒ FastAPI 会把载荷**收窄**回缺省形态、**静默抹掉**该维的披露键
    # （实测：未列 `MemoryAuthoredListViewDto` 时 `filtered_out` 读不出来）。
    response_model=MemoryListViewDto | MemoryFilteredListViewDto | MemoryAuthoredListViewDto,
)
async def list_project_memory(
    project_id: str,
    request: Request,
    scope: str | None = None,
    proposed_by: str | None = None,
) -> MemoryListViewDto:
    """项目内的记忆清单（**可选**按 `scope` / `proposed_by` 筛；缺省不筛 ⇒ 既有行为逐字不变）。

    GOAL-20261010-049 EC-03：`scope` 是**声明的范围**（不是 ACL）—— `scope_note` 照旧
    明示「无 principal/多项目授权」；带了 `scope` 时另报 `filtered_out`（**不静默丢**）。

    GOAL-20261013-067 EC-02：`proposed_by`（**提议者**）是**同一形态的第二个维度** ——
    此前该参数被**静默忽略**（`?proposed_by=` 返回全量、**无任何披露** ⇒ 调用方
    **以为筛过了**）。现在与 `scope` **同形**：传 ⇒ 只出那一位的 + 报 `filtered_out`；
    **未知作者 ⇒ 空集**（**不猜**、**不**当全选）。**两维互斥**（一次只筛一维 ——
    同时传按 `scope` 优先并在**载荷**里如实报各自的值）。
    """
    reject_unknown_query_params(request)
    del project_id  # 单项目上下文；scope_note 明示无 principal 过滤
    deps: ApiDeps = get_deps(request)
    store = _store_of(deps)
    records = store.query(scope=scope, proposed_by=proposed_by)  # type: ignore[attr-defined]
    rows = _record_dtos(records)
    # 三个形态各自**显式**声明自己的键（不给路由开 `response_model_exclude_none`：那种开关
    # 会连**嵌套模型**一起递归应用，把别的读面上**有意义**的 `null` 抹掉 —— 实测过）。
    total = len(store.query())  # type: ignore[attr-defined]
    if scope is None and proposed_by is None:
        return MemoryListViewDto(records=rows, scope_note=SCOPE_NOTE)
    if proposed_by is not None:
        return MemoryAuthoredListViewDto(
            records=rows,
            scope_note=SCOPE_NOTE,
            proposed_by=proposed_by,
            filtered_out=total - len(records),
        )
    return MemoryFilteredListViewDto(
        records=rows,
        scope_note=SCOPE_NOTE,
        scope=scope,
        filtered_out=total - len(records),
    )


def _record_dtos(records: Any) -> list[MemoryRecordDto]:
    """一批记录 ⇒ 读面 DTO 列表（**四个反向索引各扫一次**，不逐条再查）。

    **为什么单列**：`list_project_memory` 有 50 行硬上限 —— 序 29/30/31 逐轮加索引之后
    一度把它顶爆 ⇒ 逐段搬到这里（**语义一字未动**，只是换落点），并守住那道门。

    四件都由**同一批记录**算出来（与编排面**同一手法**；不逐条再查 —— 那会 N+1 且
    两处看到不同的世界）：反向取代（序 18）/ 反向冲突（序 30）/ 反向消解（序 31）/
    链终点（序 21）。
    """
    reverse = superseded_by_index(records)
    conflicted_by = conflicted_by_index(records)
    resolved = resolved_pair_index(records)
    # GOAL-20261012-064 EC-03：**悬空引用**同样扫同批记录一次（同族的第四个实例）。
    dangling = dangling_reference_index(records)
    terminals = terminal_versions(records)
    return [
        _record_dto(
            record,
            facts=_RowFacts(
                superseded_by=reverse.get(record.id, []),
                terminal=dict(terminals.get(record.id) or {}),
                conflicted_by=conflicted_by.get(record.id, []),
                resolved_with=sorted(resolved.get(record.id, set())),
                dangling_supersedes=list(dangling.get(record.id, ([], []))[0]),
                dangling_contradictions=list(dangling.get(record.id, ([], []))[1]),
            ),
        )
        for record in records
    ]


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
    reject_unknown_query_params(request)
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
