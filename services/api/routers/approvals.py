"""Approvals 控制面路由（CONTROL_PLANE_API.md Tasks / Approvals 节）。

UI 不决定 Policy：decide 全由后端裁决（ApprovalRegistry + 状态机 +
If-Match）。deny → Run APPROVAL_REJECTED → FAILED；approve → APPROVAL_GRANTED
→ RUNNING；决策事件进 outbox 审计。
"""

from __future__ import annotations

from dataclasses import replace

from fastapi import APIRouter, Request

from packages.application.ports import ApprovalStore
from packages.application.ports.approval_store import ApprovalRecord
from packages.application.ports.errors import InvalidInputError
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
from services.api.approvals import (
    build_approval_event,
    decide_approval,
)
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.approvals import (
    ApprovalDecideDto,
    ApprovalDto,
    InterventionDto,
)
from services.api.errors import ApiError
from services.api.run_access import get_run_or_error, save_run

router = APIRouter(tags=["approvals"])

_ACTION_LABEL = "policy-required-action"


def _approval_dto(approval: ApprovalRecord) -> ApprovalDto:
    return ApprovalDto(
        id=approval.id,
        run_id=approval.run_id,
        action=approval.action,
        risk=approval.risk,
        context=approval.context,
        policy_source=approval.policy_source,
        status=approval.status,
        version=approval.version,
    )


def _ensure_registry(deps: ApiDeps) -> ApprovalStore:
    if deps.approvals is None:
        raise ApiError(503, "Approvals Unavailable", "approval registry not configured")
    return deps.approvals


def _require_run(deps: ApiDeps, run_id: str) -> ResearchRun:
    return get_run_or_error(deps, run_id)


@router.get("/approvals", response_model=list[ApprovalDto])
async def list_approvals(request: Request) -> list[ApprovalDto]:
    """待决审批列表（事件投影；run 处于 WAITING_FOR_APPROVAL 才可裁决）。"""
    deps: ApiDeps = get_deps(request)
    registry = _ensure_registry(deps)
    return [_approval_dto(approval) for approval in registry.list_pending()]


@router.get("/runs/{run_id}/approvals", response_model=list[ApprovalDto])
async def list_run_approvals(run_id: str, request: Request) -> list[ApprovalDto]:
    """run 审批历史（WP-B：ApprovalStore.list_for_run 已有权威面）。

    含已裁决记录（status 区分 PENDING/GRANTED/DENIED）；未知 run → 404。
    """
    deps: ApiDeps = get_deps(request)
    registry = _ensure_registry(deps)
    _require_run(deps, run_id)
    return [_approval_dto(approval) for approval in registry.list_for_run(run_id)]


@router.post("/approvals/{approval_id}/decide", response_model=ApprovalDto)
async def decide(approval_id: str, payload: ApprovalDecideDto, request: Request) -> ApprovalDto:
    """后端裁决（hidden button != authorization）：

    - duplicate decide → 409；approve-vs-deny race → 后者 409；
    - stale If-Match → 412；run 非 WAITING_FOR_APPROVAL → 409；
    - deny → Run APPROVAL_REJECTED（FAILED）；approve → APPROVAL_GRANTED（RUNNING）
      并续跑 human gate 暂停的剩余执行（WP-H）；
    - 执行上下文不可恢复（如进程重启后）→ 503，decision 不写入、不伪装恢复；
    - 决策事件（approval.decided）落 outbox 审计。
    """
    deps: ApiDeps = get_deps(request)
    registry = _ensure_registry(deps)
    approval = _approval_or_404(deps, approval_id)
    run_id = approval.run_id
    run = _require_run(deps, run_id)
    _require_resumable(deps, payload, run, approval)
    decided = decide_approval(
        registry=registry,
        approval_id=approval_id,
        decision=payload.decision,
        if_match=request.headers.get("If-Match"),
        run=run,
    )
    transition = (
        ResearchRunState.Transition.APPROVAL_GRANTED
        if payload.decision == "approve"
        else ResearchRunState.Transition.APPROVAL_REJECTED
    )
    try:
        updated_run = run.transition(transition)
    except ValueError as exc:
        raise ApiError(409, "Invalid Transition", str(exc)) from exc
    save_run(deps, updated_run)
    event = build_approval_event(decided, actor="user:console")
    deps.events.publish(event)
    if payload.decision == "approve":
        _resume_after_approval(deps, run_id, updated_run)
    return _approval_dto(decided)


def _approval_or_404(deps: ApiDeps, approval_id: str) -> ApprovalRecord:
    approval = deps.approvals.get(approval_id) if deps.approvals is not None else None
    if approval is None:
        raise ApiError(404, "Not Found", f"approval not found: {approval_id}")
    return approval


def _require_resumable(
    deps: ApiDeps, payload: ApprovalDecideDto, run: ResearchRun, approval: ApprovalRecord
) -> None:
    """orchestration 的 human-gate 暂停在 approve 前要求可恢复执行上下文；
    非 orchestration 审批（action 无 human-gate 前缀）只记录裁决、无续跑语义。"""
    if payload.decision != "approve" or deps.runs is None:
        return
    if not approval.action.startswith("human-gate:"):
        return
    if run.state == ResearchRunState.State.WAITING_FOR_APPROVAL and not (
        deps.runs.has_waiting_context(run.id.value)
    ):
        raise ApiError(
            503,
            "Execution Context Lost",
            "the run's paused execution context is unavailable in this process "
            "(e.g. after restart); the approval is not consumed and no fake resume occurs",
        )


def _resume_after_approval(deps: ApiDeps, run_id: str, granted: ResearchRun) -> None:
    """续跑 human-gate 暂停；无暂存上下文（非 orchestration 审批竞态/重启）为
    no-op：decision 已按 canonical 状态机落库，绝不伪造续跑。"""
    if deps.runs is None:
        return
    try:
        outcome = deps.runs.resume_after_approval(run_id)
    except InvalidInputError:
        return
    save_run(deps, replace(granted, state=outcome.state))


@router.post("/runs/{run_id}/pause", response_model=object)
async def pause_run(run_id: str, request: Request) -> object:
    """干预：pause（RUNNING → PAUSED；正式状态机迁移）。"""
    deps: ApiDeps = get_deps(request)
    run = _require_run(deps, run_id)
    try:
        updated = run.transition(ResearchRunState.Transition.PAUSE)
    except ValueError as exc:
        raise ApiError(409, "Invalid Transition", str(exc)) from exc
    save_run(deps, updated)
    return _run_payload(updated)


@router.post("/runs/{run_id}/resume", response_model=object)
async def resume_run(run_id: str, request: Request) -> object:
    """干预：resume（PAUSED → RUNNING；正式状态机迁移）。"""
    deps: ApiDeps = get_deps(request)
    run = _require_run(deps, run_id)
    try:
        updated = run.transition(ResearchRunState.Transition.RESUME)
    except ValueError as exc:
        raise ApiError(409, "Invalid Transition", str(exc)) from exc
    save_run(deps, updated)
    return _run_payload(updated)


@router.post("/runs/{run_id}/interventions", response_model=object)
async def intervene(run_id: str, payload: InterventionDto, request: Request) -> object:
    """干预：按 kind 分支（M13-R1 WP-P2）。

    - pause / resume：走正式状态机迁移；
    - budget_adjust / replace_agent（语义变更）：必须产生 Manifest
      Revision / Fork，M13 诚实返回 501，不再无条件吞掉 payload 改 PAUSE。
    """
    deps: ApiDeps = get_deps(request)
    run = _require_run(deps, run_id)
    if payload.kind == "pause":
        try:
            updated = run.transition(ResearchRunState.Transition.PAUSE)
        except ValueError as exc:
            raise ApiError(409, "Invalid Transition", str(exc)) from exc
        save_run(deps, updated)
        return _run_payload(updated)
    if payload.kind == "resume":
        try:
            updated = run.transition(ResearchRunState.Transition.RESUME)
        except ValueError as exc:
            raise ApiError(409, "Invalid Transition", str(exc)) from exc
        save_run(deps, updated)
        return _run_payload(updated)
    raise ApiError(
        501,
        "Semantic Intervention Pending",
        "运行中语义变更必须产生 Manifest Revision / Fork；持久化属 M14",
    )


def _run_payload(run: ResearchRun) -> dict[str, object]:
    return {
        "id": run.id.value,
        "state": run.state,
        "manifest_digest": str(run.manifest_digest) if run.manifest_digest else None,
    }
