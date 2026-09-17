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
from packages.application.run_orchestration.budget_adjust import (
    AdjustmentCommand,
    AdjustmentLine,
    BudgetAdjustmentError,
    execute_budget_adjustment,
)
from packages.domain.budget import BudgetPolicy, ResourceType
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
from services.api.approvals import (
    build_approval_event,
    decide_approval,
)
from services.api.catalog_merge import merged_catalog_snapshot, merged_project_settings
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.approvals import (
    ApprovalDecideDto,
    ApprovalDto,
    InterventionDto,
)
from services.api.errors import ApiError
from services.api.run_access import get_run_or_error, save_run
from services.api.run_resume import rebuild_and_resume

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
    """干预：pause（RUNNING → PAUSED）——协作式暂停，不是"只改状态"。

    canonical 状态即暂停事实：派发面据此停止向 worker 认领该 run 的任务
    （已持租约不撤销）；本进程若正持有该 run 的执行上下文，执行器会在下一次
    phase 组边界读到该状态并停止派发（零任务执行）。
    """
    deps: ApiDeps = get_deps(request)
    run = _require_run(deps, run_id)
    updated = _transition_or_409(run, ResearchRunState.Transition.PAUSE)
    save_run(deps, updated)
    return _pause_payload(deps, updated)


@router.post("/runs/{run_id}/resume", response_model=object)
async def resume_run(run_id: str, request: Request) -> object:
    """干预：resume（PAUSED → RUNNING）。

    派发恢复是确定的；**继续执行**只在本进程持有暂停上下文时发生，否则响应
    明说 `continuation=NONE`——不把"解除暂停"伪装成"续跑"。
    """
    deps: ApiDeps = get_deps(request)
    run = _require_run(deps, run_id)
    updated = _transition_or_409(run, ResearchRunState.Transition.RESUME)
    save_run(deps, updated)
    return _resume_payload(deps, run_id, updated)


def _transition_or_409(run: ResearchRun, transition: str) -> ResearchRun:
    try:
        return run.transition(transition)
    except ValueError as exc:
        raise ApiError(409, "Invalid Transition", str(exc)) from exc


def _pause_payload(deps: ApiDeps, run: ResearchRun) -> dict[str, object]:
    payload = _run_payload(run)
    payload["dispatch"] = "HELD"
    payload["execution_context"] = (
        "PAUSED_IN_PROCESS" if _has_paused_context(deps, run.id.value) else "NONE"
    )
    payload["note"] = "cooperative pause: no new task dispatch; leases already held are not revoked"
    return payload


def _resume_payload(deps: ApiDeps, run_id: str, run: ResearchRun) -> dict[str, object]:
    """resume 的三种结局（都如实表达，不把"解除暂停"伪装成"续跑"）：

    1. 本进程持有暂停上下文 ⇒ `RESUMED`（真的执行剩余任务）；
    2. 没有本进程上下文（重启后）⇒ 按 run 记下的装配来源**重建**后续跑（GOAL-003
       cycle 20）⇒ `REBUILT`；重建被诚实拒绝（来源缺失/不可解析/preflight 不过/
       语义漂移）⇒ `NONE` + 点名原因，canonical 状态不动（resume 的既有语义是
       "恢复派发"，一次失败的续跑不该把这个闸门重新关上）；
    3. 连服务都没装配 ⇒ `NONE`（既有行为）。
    """
    payload = _run_payload(run)
    payload["dispatch"] = "RELEASED"
    payload["continuation"] = "NONE"
    if deps.runs is None:
        payload["note"] = (
            "no paused execution context in this process; dispatch resumes, "
            "and no continuation was pending"
        )
        return payload
    if deps.runs.has_paused_context(run_id):
        try:
            outcome = deps.runs.resume_paused(run_id, run)
        except InvalidInputError:  # 竞态：上下文已被另一次 resume 取走
            payload["note"] = "paused execution context was already consumed"
            return payload
        except Exception as exc:  # noqa: BLE001 - 续跑失败 ⇒ 补偿，不吞掉
            # GOAL-004 cycle 7（EC-06）：续跑失败不留悬空 RUNNING。放回 PAUSED 并记原因
            # （事件链）；响应如实说 `FAILED` + 原因，而 run 行是停车态（不是 RUNNING）。
            compensated = deps.runs.compensate_failed_resume(run, exc)
            save_run(deps, compensated)
            payload = _run_payload(compensated)
            payload["dispatch"] = "HELD"
            payload["continuation"] = "FAILED"
            payload["note"] = (
                "resume failed and the run was compensated back to PAUSED: "
                f"{type(exc).__name__}: {exc}"
            )
            return payload
        resumed = replace(run, state=outcome.state)
        save_run(deps, resumed)
        payload = _run_payload(resumed)
        payload["dispatch"] = "RELEASED"
        payload["continuation"] = "RESUMED"
        payload["note"] = "paused execution context resumed; remaining tasks executed"
        return payload
    return _rebuilt_payload(deps, run)


def _rebuilt_payload(deps: ApiDeps, run: ResearchRun) -> dict[str, object]:
    """重启后的续跑：按 run 记下的装配来源重建上下文。

    重建被诚实拒绝时**不动 canonical 状态**：resume 的既有语义是"恢复派发"
    （PAUSED 是派发面的闸门），重建失败不该把闸门重新关上；这里的职责是把原因
    如实说出来，而不是把 run 挂回停车状态——那留给控制面（`POST /pause`）。
    """
    attempt = rebuild_and_resume(deps, run)
    if not attempt.resumed:
        payload = _run_payload(run)
        payload["dispatch"] = "RELEASED"
        payload["continuation"] = "NONE"
        payload["note"] = (
            f"no paused execution context in this process; rebuild refused: {attempt.refusal}"
        )
        return payload
    resumed = replace(run, state=attempt.outcome.state if attempt.outcome else run.state)
    save_run(deps, resumed)
    payload = _run_payload(resumed)
    payload["dispatch"] = "RELEASED"
    payload["continuation"] = "REBUILT"
    payload["note"] = (
        "execution context rebuilt from the recorded protocol source; remaining tasks executed"
    )
    return payload


def _has_paused_context(deps: ApiDeps, run_id: str) -> bool:
    return deps.runs is not None and deps.runs.has_paused_context(run_id)


@router.post("/runs/{run_id}/interventions", response_model=object)
async def intervene(run_id: str, payload: InterventionDto, request: Request) -> object:
    """干预：按 kind 分支（M13-R1 WP-P2；PLAN-046 扩展 budget_adjust）。

    - pause / resume：走正式状态机迁移；
    - budget_adjust：走 BudgetLedger 正式面（release 既有预留 + reserve 新额度）；
      预算面缺失 503，无调整行 422；
    - replace_agent（语义变更）：必须产生 Manifest Revision / Fork，诚实 501。
    """
    deps: ApiDeps = get_deps(request)
    run = _require_run(deps, run_id)
    if payload.kind == "pause":
        updated = _transition_or_409(run, ResearchRunState.Transition.PAUSE)
        save_run(deps, updated)
        return _pause_payload(deps, updated)
    if payload.kind == "resume":
        updated = _transition_or_409(run, ResearchRunState.Transition.RESUME)
        save_run(deps, updated)
        return _resume_payload(deps, run_id, updated)
    if payload.kind == "budget_adjust":
        return _budget_adjust(deps, run_id, payload)
    raise ApiError(
        501,
        "Semantic Intervention Pending",
        "运行中语义变更必须产生 Manifest Revision / Fork；持久化属 M14",
    )


def _budget_adjust(deps: ApiDeps, run_id: str, payload: InterventionDto) -> dict[str, object]:
    """budget_adjust：release 既有预留 + reserve 新额度（run 作用域）。

    策略沿用 run 启动时的 project budget policy（catalog 解析）；既有预留
    引用来自编排服务进程内记账，跨进程重启丢失时诚实按"无既有预留"处理。
    """
    if not payload.adjustments:
        raise ApiError(422, "Empty Adjustment", "budget_adjust requires adjustments[]")
    if deps.runs is None:
        raise ApiError(503, "Run Orchestration Unavailable", "run service not configured")
    project_id = _require_run(deps, run_id).project_id
    command = AdjustmentCommand(
        run_id=run_id,
        policy=_budget_policy(deps, project_id),
        existing_ref=deps.runs.reservation_ref(run_id),
        lines=_adjustment_lines(payload),
    )
    try:
        outcome = execute_budget_adjustment(deps.budget, command)
    except BudgetAdjustmentError as exc:
        raise ApiError(503, "Budget Ledger Unavailable", str(exc)) from exc
    except ValueError as exc:
        raise ApiError(422, "Invalid Adjustment", str(exc)) from exc
    deps.runs.register_reservation_ref(run_id, outcome.reservation_ref)
    return {
        "run_id": run_id,
        "released_ref": outcome.released_ref,
        "reservation_ref": outcome.reservation_ref,
        "reservations": [
            {
                "id": item.id,
                "scope": item.scope,
                "resource_type": item.resource_type.value,
                "quantity": item.quantity,
                "unit": item.unit,
            }
            for item in outcome.reservations
        ],
    }


def _budget_policy(deps: ApiDeps, project_id: str) -> BudgetPolicy:
    """resolve 项目预算策略；缺失 503（不落默认策略、不静默放行）。"""
    settings = merged_project_settings(deps, project_id)
    policy = merged_catalog_snapshot(deps).budget_policies.get(settings.budget_policy_id)
    if policy is None:
        raise ApiError(
            503,
            "Budget Policy Unavailable",
            f"budget policy {settings.budget_policy_id} is not resolvable",
        )
    return policy


def _adjustment_lines(payload: InterventionDto) -> tuple[AdjustmentLine, ...]:
    """DTO 调整行 → 应用层调整行；未知 resource_type 由 ResourceType 报错（422）。"""
    return tuple(
        AdjustmentLine(
            resource_type=ResourceType(line.resource_type),
            quantity=line.quantity,
            unit=line.unit,
        )
        for line in payload.adjustments
    )


def _run_payload(run: ResearchRun) -> dict[str, object]:
    return {
        "id": run.id.value,
        "state": run.state,
        "manifest_digest": str(run.manifest_digest) if run.manifest_digest else None,
    }
