"""Approvals 控制面路由（CONTROL_PLANE_API.md Tasks / Approvals 节）。

UI 不决定 Policy：decide 全由后端裁决（ApprovalRegistry + 状态机 +
If-Match）。deny → Run APPROVAL_REJECTED → FAILED；approve → APPROVAL_GRANTED
→ RUNNING；决策事件进 outbox 审计。
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
from services.api.approvals import (
    ApprovalRegistry,
    PendingApproval,
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

router = APIRouter(tags=["approvals"])

_ACTION_LABEL = "policy-required-action"


def _approval_dto(approval: PendingApproval) -> ApprovalDto:
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


def _ensure_registry(deps: ApiDeps) -> ApprovalRegistry:
    if deps.approvals is None:
        raise ApiError(503, "Approvals Unavailable", "approval registry not configured")
    return deps.approvals


def _require_run(deps: ApiDeps, run_id: str) -> ResearchRun:
    run = deps.run_registry.get(run_id)
    if run is None:
        raise ApiError(404, "Not Found", f"run not found: {run_id}")
    return run


@router.get("/approvals", response_model=list[ApprovalDto])
async def list_approvals(request: Request) -> list[ApprovalDto]:
    """待决审批列表（事件投影；run 处于 WAITING_FOR_APPROVAL 才可裁决）。"""
    deps: ApiDeps = get_deps(request)
    registry = _ensure_registry(deps)
    return [_approval_dto(approval) for approval in registry.list_pending()]


@router.post("/approvals/{approval_id}/decide", response_model=ApprovalDto)
async def decide(approval_id: str, payload: ApprovalDecideDto, request: Request) -> ApprovalDto:
    """后端裁决（hidden button != authorization）：

    - duplicate decide → 409；approve-vs-deny race → 后者 409；
    - stale If-Match → 412；run 非 WAITING_FOR_APPROVAL → 409；
    - deny → Run APPROVAL_REJECTED（FAILED）；approve → APPROVAL_GRANTED（RUNNING）；
    - 决策事件（approval.decided）落 outbox 审计。
    """
    deps: ApiDeps = get_deps(request)
    registry = _ensure_registry(deps)
    run_id = _run_id_of(deps, approval_id)
    run = _require_run(deps, run_id)
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
    deps.run_registry[run_id] = updated_run
    event = build_approval_event(decided, actor="user:console")
    deps.events.publish(event)
    return _approval_dto(decided)


def _run_id_of(deps: ApiDeps, approval_id: str) -> str:
    approval = deps.approvals.get(approval_id) if deps.approvals is not None else None
    if approval is None:
        raise ApiError(404, "Not Found", f"approval not found: {approval_id}")
    return approval.run_id


@router.post("/runs/{run_id}/pause", response_model=object)
async def pause_run(run_id: str, request: Request) -> object:
    """干预：pause（RUNNING → PAUSED；正式状态机迁移）。"""
    deps: ApiDeps = get_deps(request)
    run = _require_run(deps, run_id)
    try:
        updated = run.transition(ResearchRunState.Transition.PAUSE)
    except ValueError as exc:
        raise ApiError(409, "Invalid Transition", str(exc)) from exc
    deps.run_registry[run_id] = updated
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
    deps.run_registry[run_id] = updated
    return _run_payload(updated)


@router.post("/runs/{run_id}/interventions", response_model=object)
async def intervene(run_id: str, payload: InterventionDto, request: Request) -> object:
    """干预：budget adjustment / future-agent replacement。

    运行中修改 Model/Tool/semantic 配置必须产生 Manifest Revision / Fork，
    不得 silent mutation；持久化配置修改属 M14。本端点对语义变更返回
    501（诚实边界），对纯状态类（pause/resume）走正式状态机。
    """
    del payload
    deps: ApiDeps = get_deps(request)
    run = _require_run(deps, run_id)
    if run.state == ResearchRunState.State.RUNNING:
        try:
            updated = run.transition(ResearchRunState.Transition.PAUSE)
        except ValueError as exc:
            raise ApiError(409, "Invalid Transition", str(exc)) from exc
        deps.run_registry[run_id] = updated
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
