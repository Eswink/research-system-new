"""Run 生命周期控制面路由。

流程：HTTP → DTO → use case（RunOrchestrationService）→ Domain / Port。
Timeline/事件端点见 run_events.py（SSE + JSON replay 双模式）。
启动装配（协议来源 → preflight → StartRunCommand → 编排链）在
`services/api/run_execution.py`，与 G14 队列派发器共用同一实现。
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from packages.application.run_orchestration.commands import CancelRunCommand
from packages.domain.core import ID
from packages.domain.run import ResearchRun
from packages.domain.state_base import InvalidTransitionError
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.runs import DispatchOwnershipDto, RunDetailDto, RunStartDto, TaskDto
from services.api.errors import ApiError
from services.api.protocol_source import draft_ref_of
from services.api.run_access import get_run_or_error, save_run
from services.api.run_dispatch_view import (
    dispatch_ownership_dto,
    dispatch_ownership_read,
    dispatch_ownership_read_many,
)
from services.api.run_execution import (
    ExecutionRequest,
    execution_inputs,
    run_from_execution,
)
from services.api.run_execution_view import run_execution_dto
from services.api.run_pause_view import paused_dispatch_view
from services.api.run_rebuild_view import rebuild_readiness_dto

router = APIRouter(prefix="/runs", tags=["runs"])
projects_router = APIRouter(tags=["runs"])


def _detail_dto(
    deps: ApiDeps,
    run: ResearchRun,
    *,
    dispatch: DispatchOwnershipDto | None = None,
    with_execution: bool = False,
) -> RunDetailDto:
    """canonical run → 读面 DTO（详情与列表共用，停车语义只有这一处分类）。

    派发读面**每个 run 只读一次**（GOAL-004 cycle 6 = EC-05 ②）：`dispatch` 与
    `paused_dispatch` 是同一个读结果的两个视图，不是一个字段一次读。列表路径把**批量读到的**
    `dispatch` 传进来（GOAL-005 cycle 5 = EC-05 ①：不再逐 run 各读一次）；`dispatch=None`
    时本函数自己读一次（详情路径）。

    `with_execution`（GOAL-007 cycle 4 = EC-04）**只由详情路径开启**：执行体读面要回读该
    run 的冻结事件，列表路径逐 run 回读会变成 N+1。默认 False 让「哪条路径披露什么」是
    显式的，不靠 `dispatch is None` 这种巧合。
    """
    if dispatch is None:
        dispatch = dispatch_ownership_dto(dispatch_ownership_read(deps.workflow, run.id.value))
    projection = deps.projection
    execution = (
        run_execution_dto(projection, run.id.value)
        if with_execution and projection is not None
        else None
    )
    return RunDetailDto(
        id=run.id.value,
        project_id=run.project_id,
        protocol_id=run.protocol_id,
        state=run.state,
        manifest_digest=str(run.manifest_digest) if run.manifest_digest else None,
        manifest_semantic_digest=(
            str(run.manifest_semantic_digest) if run.manifest_semantic_digest else None
        ),
        protocol_body_digest=str(run.protocol_body.digest) if run.protocol_body else None,
        paused_dispatch=paused_dispatch_view(run.state, dispatch),
        dispatch=dispatch,
        rebuild=rebuild_readiness_dto(run),
        execution=execution,
        created_at=run.created_at.value.isoformat(),
        updated_at=run.updated_at.value.isoformat(),
    )


def _run_state_dto(deps: ApiDeps, run_id: str) -> RunDetailDto:
    """启动/取消后的详情读面（与 `GET /runs/{id}` 同一条路径，含执行体披露）。"""
    return _detail_dto(deps, get_run_or_error(deps, run_id), with_execution=True)


@projects_router.post("/projects/{project_id}/runs", response_model=RunDetailDto)
async def start_run(project_id: str, payload: RunStartDto, request: Request) -> RunDetailDto:
    """启动一次 Research Run（StartRunCommand → 正式编排链；path 或草稿修订引用）。

    运行归属路径 project_id（WP-B）：preflight 夹具覆盖场景下 settings 仍为
    夹具项目（受控测试态），注册项目行的 project_id 与路径一致。
    """
    deps: ApiDeps = get_deps(request)
    run_id = ID.generate()
    draft_ref = draft_ref_of(payload.draft_id, payload.draft_revision)
    req = ExecutionRequest(
        deps, payload.protocol_path, run_id, payload.trace_id, draft_ref, project_id
    )
    inputs = execution_inputs(req)
    run = run_from_execution(deps, run_id, inputs.project.project_id, inputs.protocol.id, inputs)
    save_run(deps, run)
    return _run_state_dto(deps, run_id.value)


@projects_router.get("/projects/{project_id}/runs", response_model=list[RunDetailDto])
async def list_runs(project_id: str, request: Request) -> list[RunDetailDto]:
    """Run 列表（created_at 倒序；M13-R1 WP-M2：刷新恢复入口）。

    每行的 `dispatch` 与 `GET /runs/{id}` 同一判据：整页由**一次**批量读回答，
    不随列表长度放大成 N 次内部读。
    """
    scope_project_id = project_id
    deps: ApiDeps = get_deps(request)
    if deps.runs_store is None:
        # 注册表回退（测试注入）同样按项目过滤（WP-B：不跨项目泄漏）。
        runs = [
            run
            for run in reversed(list(deps.run_registry.values()))
            if run.project_id == scope_project_id
        ]
    else:
        runs = list(deps.runs_store.list_runs(scope_project_id))
    dispatch_by_run = dispatch_ownership_read_many(
        deps.workflow, tuple(run.id.value for run in runs)
    )
    return [
        _detail_dto(
            deps,
            run,
            dispatch=dispatch_ownership_dto(dispatch_by_run.get(run.id.value)),
        )
        for run in runs
    ]


@router.get("/{run_id}", response_model=RunDetailDto)
async def get_run(run_id: str, request: Request) -> RunDetailDto:
    """Run 状态视图（canonical state；刷新后从 API 恢复）。"""
    deps: ApiDeps = get_deps(request)
    return _run_state_dto(deps, run_id)


@router.post("/{run_id}/cancel", response_model=RunDetailDto)
async def cancel_run(run_id: str, request: Request) -> RunDetailDto:
    """协作式取消（幂等）；非法状态机迁移 → 409。"""
    deps: ApiDeps = get_deps(request)
    if deps.runs is None:
        raise ApiError(503, "Run Orchestration Unavailable", "run service not configured")
    run = get_run_or_error(deps, run_id)
    try:
        deps.runs.cancel_run(CancelRunCommand(run_id=ID(run_id)))
        cancelled = run.transition("CANCEL")
        save_run(deps, cancelled)
    except InvalidTransitionError as exc:
        raise ApiError(409, "Invalid Transition", str(exc)) from exc
    except ValueError as exc:
        raise ApiError(409, "Invalid Transition", str(exc)) from exc
    return _run_state_dto(deps, run_id)


@router.get("/{run_id}/tasks", response_model=list[TaskDto])
async def list_run_tasks(run_id: str, request: Request) -> list[TaskDto]:
    """run 任务投影（canonical state 读取，非审计事件）。"""
    deps: ApiDeps = get_deps(request)
    get_run_or_error(deps, run_id)
    if deps.projection is None:
        raise ApiError(503, "Projection Unavailable", "run projection not configured")
    rows = deps.projection.list_tasks(run_id)
    return [
        TaskDto(
            task_id=task.id.value,
            contract_id=contract.id,
            agent_id=task.assigned_agent_id,
            status=task.status,
            attempt=task.attempt,
        )
        for task, contract in rows
    ]
