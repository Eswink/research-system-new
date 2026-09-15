"""G14 实验队列控制面路由：入队 / 列表 / 改期 / 取消 + 计划列表。

语义要点（与 `docs/frontend/CONSOLE_PAGE_MAP.md` G14 行一致）：

- 入队时**即解析协议来源**（未知路径/草稿 → 404，来源缺失或二义 → 422）：
  不让坏引用在队列里等到派发才失败。
- 计划已归档（ARCHIVED）→ 409：归档是计划的终态，不再是可启动对象。
- 派发由控制面的队列消费者完成（`services.api.experiment_queue`），本路由只写
  canonical state（条目行）；`not_before` 是**排期事实**不是延迟实现。
- 改期/取消只作用于 QUEUED；其它状态 → 409（DISPATCHING 已在启动中，处置该
  run 用 run 的 cancel 面；DISPATCHED 已经是启动事实，取消毫无意义）。
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Request

from packages.domain.core import ID, Timestamp
from packages.domain.experiment_queue import ExperimentQueueEntry, QueueProtocolSource
from packages.domain.experiment_state import ExperimentPlanState
from packages.domain.experiments import ExperimentPlan
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.experiments import (
    ExperimentPlanDto,
    ExperimentQueueEnqueueDto,
    ExperimentQueueEntryDto,
    ExperimentQueueRescheduleDto,
    ExperimentQueueViewDto,
)
from services.api.errors import ApiError
from services.api.protocol_source import load_protocol_for_source

router = APIRouter(tags=["experiments"])

DISPATCH_NOTE = (
    "派发由控制面队列消费者按排期执行：与 POST /runs 同一条装配链，进程内同步执行、"
    "串行推进；认领过期（进程中断）的条目会重新派发（at-least-once）。"
    "取消/改期只作用于 QUEUED。"
)


def _store_of(deps: ApiDeps) -> object:
    if deps.experiment_store is None:
        raise ApiError(
            503,
            "Experiment Store Unavailable",
            "experiment store not configured",
        )
    return deps.experiment_store


def _plan_of(store: object, plan_id: str) -> ExperimentPlan:
    try:
        plan: ExperimentPlan = store.get_plan(plan_id)  # type: ignore[attr-defined]
    except Exception as exc:  # noqa: BLE001 - InvalidInputError 统一映射 404
        raise ApiError(404, "Experiment Plan Not Found", f"unknown plan id: {plan_id}") from exc
    return plan


def _entry_of(store: object, entry_id: str) -> ExperimentQueueEntry:
    try:
        entry: ExperimentQueueEntry = store.get_queue_entry(entry_id)  # type: ignore[attr-defined]
    except Exception as exc:  # noqa: BLE001 - InvalidInputError 统一映射 404
        raise ApiError(404, "Queue Entry Not Found", f"unknown queue entry id: {entry_id}") from exc
    return entry


def parse_timestamp(value: str | None, *, field: str) -> Timestamp | None:
    """ISO-8601 → domain Timestamp（必须带时区；非 UTC 输入按 UTC 归一）。"""
    if value is None or value.strip() == "":
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ApiError(422, "Invalid Timestamp", f"{field} must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ApiError(422, "Invalid Timestamp", f"{field} must carry a timezone offset")
    return Timestamp(parsed.astimezone(timezone.utc))


def _source_of(payload: ExperimentQueueEnqueueDto) -> QueueProtocolSource:
    try:
        return QueueProtocolSource(
            protocol_path=payload.protocol_path,
            draft_id=payload.draft_id,
            draft_revision=payload.draft_revision,
        )
    except ValueError as exc:
        raise ApiError(422, "Invalid Protocol Source", str(exc)) from exc


def _entry_dto(entry: ExperimentQueueEntry, plan_name: str | None) -> ExperimentQueueEntryDto:
    return ExperimentQueueEntryDto(
        id=entry.id.value,
        project_id=entry.project_id,
        plan_id=entry.plan_id.value,
        plan_name=plan_name,
        protocol_path=entry.source.protocol_path,
        draft_id=entry.source.draft_id,
        draft_revision=entry.source.draft_revision,
        state=entry.state,
        not_before=entry.not_before.value.isoformat() if entry.not_before else None,
        claimed_at=entry.claimed_at.value.isoformat() if entry.claimed_at else None,
        run_id=entry.run_id,
        failure_reason=entry.failure_reason,
        created_at=entry.created_at.value.isoformat(),
        updated_at=entry.updated_at.value.isoformat(),
    )


def plan_dto(plan: ExperimentPlan) -> ExperimentPlanDto:
    return ExperimentPlanDto(
        id=plan.id.value,
        name=plan.name,
        hypothesis=plan.hypothesis,
        task_contract_ref=plan.task_contract_ref,
        input_spec_digest=str(plan.input_spec_digest) if plan.input_spec_digest else None,
        state=plan.state,
        created_at=plan.created_at.value.isoformat(),
        updated_at=plan.updated_at.value.isoformat(),
    )


@router.get("/experiment-plans", response_model=list[ExperimentPlanDto])
async def list_experiment_plans(
    request: Request, state: str | None = None
) -> list[ExperimentPlanDto]:
    """计划列表（新→旧）；`state` 过滤按域取值（DRAFT/PREREGISTERED/ARCHIVED）。

    列为域面无项目归属（ExperimentPlan 无 project_id），因此按全局返回——
    与 `GAPS.multiProject` 的诚实标注一致，不伪装项目隔离。
    """
    deps: ApiDeps = get_deps(request)
    store = _store_of(deps)
    plans: list[ExperimentPlan] = store.list_plans(state=state)  # type: ignore[attr-defined]
    return [plan_dto(plan) for plan in plans]


@router.post(
    "/projects/{project_id}/experiments/{plan_id}/queue",
    response_model=ExperimentQueueEntryDto,
    status_code=201,
)
async def enqueue_experiment_run(
    project_id: str,
    plan_id: str,
    payload: ExperimentQueueEnqueueDto,
    request: Request,
) -> ExperimentQueueEntryDto:
    """把一次实验启动请求入队（来源立即解析；可带 not_before 排期）。"""
    deps: ApiDeps = get_deps(request)
    store = _store_of(deps)
    plan = _plan_of(store, plan_id)
    if plan.state == ExperimentPlanState.State.ARCHIVED:
        raise ApiError(
            409, "Experiment Plan Archived", f"plan {plan_id} is ARCHIVED and cannot be queued"
        )
    source = _source_of(payload)
    # 立即解析：坏引用在入队时暴露，不在派发时才失败。
    load_protocol_for_source(deps, source.protocol_path, source.draft_ref)
    entry = ExperimentQueueEntry(
        id=ID.generate(),
        project_id=project_id,
        plan_id=ID(plan_id),
        source=source,
        not_before=parse_timestamp(payload.not_before, field="not_before"),
    )
    store.save_queue_entry(entry)  # type: ignore[attr-defined]
    return _entry_dto(entry, plan.name)


@router.get("/projects/{project_id}/experiment-queue", response_model=ExperimentQueueViewDto)
async def project_experiment_queue(project_id: str, request: Request) -> ExperimentQueueViewDto:
    """项目队列视图（新→旧）；计划名从计划表补齐（缺失则 None，不伪造）。"""
    deps: ApiDeps = get_deps(request)
    store = _store_of(deps)
    names = {plan.id.value: plan.name for plan in store.list_plans()}  # type: ignore[attr-defined]
    entries: list[ExperimentQueueEntry] = store.list_queue_entries(  # type: ignore[attr-defined]
        project_id
    )
    return ExperimentQueueViewDto(
        entries=[_entry_dto(entry, names.get(entry.plan_id.value)) for entry in entries],
        dispatch_note=DISPATCH_NOTE,
    )


@router.patch("/experiment-queue/{entry_id}", response_model=ExperimentQueueEntryDto)
async def reschedule_queue_entry(
    entry_id: str, payload: ExperimentQueueRescheduleDto, request: Request
) -> ExperimentQueueEntryDto:
    """改期（只对 QUEUED）；空值清除排期（立即到期）。"""
    deps: ApiDeps = get_deps(request)
    store = _store_of(deps)
    not_before = parse_timestamp(payload.not_before, field="not_before")
    try:
        updated: ExperimentQueueEntry = store.reschedule_queue_entry(  # type: ignore[attr-defined]
            entry_id, not_before=not_before, now=Timestamp.now()
        )
    except Exception as exc:  # noqa: BLE001 - 未知 id 404 / 状态冲突 409
        raise _queue_error(store, entry_id, exc) from exc
    return _entry_dto(updated, _plan_name(store, updated))


@router.delete("/experiment-queue/{entry_id}", response_model=ExperimentQueueEntryDto)
async def cancel_queue_entry(entry_id: str, request: Request) -> ExperimentQueueEntryDto:
    """取消（只对 QUEUED）；其余状态 409（已在启动中的处置该 run）。"""
    deps: ApiDeps = get_deps(request)
    store = _store_of(deps)
    try:
        cancelled: ExperimentQueueEntry = store.cancel_queue_entry(  # type: ignore[attr-defined]
            entry_id, now=Timestamp.now()
        )
    except Exception as exc:  # noqa: BLE001 - 未知 id 404 / 状态冲突 409
        raise _queue_error(store, entry_id, exc) from exc
    return _entry_dto(cancelled, _plan_name(store, cancelled))


def _plan_name(store: object, entry: ExperimentQueueEntry) -> str | None:
    try:
        return _plan_of(store, entry.plan_id.value).name
    except ApiError:
        return None


def _queue_error(store: object, entry_id: str, exc: Exception) -> ApiError:
    """存储冲突 → HTTP：条目不存在 404，状态不允许 409（错误分类在存储层）。"""
    try:
        store.get_queue_entry(entry_id)  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001 - 读不到即不存在
        return ApiError(404, "Queue Entry Not Found", f"unknown queue entry id: {entry_id}")
    return ApiError(409, "Invalid Queue Transition", str(exc))
