"""Run 生命周期控制面路由。

流程：HTTP → DTO → use case（RunOrchestrationService）→ Domain / Port。
Timeline/事件端点见 run_events.py（SSE + JSON replay 双模式）。
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import APIRouter, Request

from packages.application.ports import CatalogSnapshot, PreflightContext, ProjectSettings
from packages.application.run_orchestration.commands import CancelRunCommand, StartRunCommand
from packages.domain.core import ID, Digest
from packages.domain.protocols import ProtocolDefinition
from packages.domain.run import ResearchRun
from packages.domain.state_base import InvalidTransitionError
from services.api.catalog_merge import merged_catalog_snapshot, merged_project_settings
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.runs import RunDetailDto, RunStartDto, TaskDto
from services.api.errors import ApiError
from services.api.preflight_support import (
    build_endpoint_health,
    build_policy_evaluator,
    build_provider_health,
)
from services.api.protocol_source import draft_ref_of, load_protocol_for_source
from services.api.routers.run_events import events_of
from services.api.run_access import get_run_or_error, save_run

router = APIRouter(prefix="/runs", tags=["runs"])
projects_router = APIRouter(tags=["runs"])


def _run_state_dto(deps: ApiDeps, run_id: str) -> RunDetailDto:
    run = get_run_or_error(deps, run_id)
    manifest = str(run.manifest_digest) if run.manifest_digest else None
    return RunDetailDto(
        id=run.id.value,
        project_id=run.project_id,
        protocol_id=run.protocol_id,
        state=run.state,
        manifest_digest=manifest,
        created_at=run.created_at.value.isoformat(),
        updated_at=run.updated_at.value.isoformat(),
    )


def _frozen_manifest_refs_of(
    deps: ApiDeps,
    run_id: str,
) -> tuple[str | None, str | None, str | None]:
    """从冻结事件恢复 manifest 与 pricing 引用（失败收敛路径）。"""
    if deps.projection is None:
        return None, None, None
    for envelope in events_of(deps.projection, run_id):
        if envelope.event_type.value == "manifest.frozen":
            digest = envelope.payload.get("digest")
            pricing_version = envelope.payload.get("pricing_version")
            pricing_digest = envelope.payload.get("pricing_digest")
            return (
                digest if isinstance(digest, str) else None,
                pricing_version if isinstance(pricing_version, str) else None,
                pricing_digest if isinstance(pricing_digest, str) else None,
            )
    return None, None, None


def _frozen_manifest_digest_of(deps: ApiDeps, run_id: str) -> str | None:
    """兼容读取冻结事件的 manifest digest。"""
    return _frozen_manifest_refs_of(deps, run_id)[0]


def _run_from_execution(
    deps: ApiDeps,
    run_id: ID,
    project_id: str,
    protocol_id: str,
    inputs: ExecutionInputs,
) -> ResearchRun:
    """执行链结果 → run 实体（执行期 ValueError 收敛 FAILED + 保留 frozen digest）。"""
    if deps.runs is None:
        raise ApiError(503, "Run Orchestration Unavailable", "run service not configured")
    try:
        outcome = deps.runs.start_run(
            inputs.protocol, inputs.catalog, inputs.project, inputs.preflight, inputs.command
        )
        return ResearchRun(
            id=run_id,
            project_id=project_id,
            protocol_id=protocol_id,
            state=outcome.state,
            manifest_digest=Digest.parse(outcome.manifest_digest)
            if outcome.manifest_digest
            else None,
            pricing_version=outcome.pricing_version,
            pricing_digest=outcome.pricing_digest,
        )
    except ValueError:
        frozen_digest, pricing_version, pricing_digest = _frozen_manifest_refs_of(
            deps, run_id.value
        )
        return ResearchRun(
            id=run_id,
            project_id=project_id,
            protocol_id=protocol_id,
            state="FAILED",
            manifest_digest=Digest.parse(frozen_digest) if frozen_digest else None,
            pricing_version=pricing_version,
            pricing_digest=pricing_digest,
        )


@dataclass(frozen=True, slots=True)
class ExecutionInputs:
    """start_run 执行输入聚合（参数对象，规避参数爆发）。"""

    protocol: ProtocolDefinition
    catalog: CatalogSnapshot
    project: ProjectSettings
    preflight: PreflightContext
    command: StartRunCommand


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    """start_run 输入参数对象（规避参数爆发）。"""

    deps: ApiDeps
    protocol_path: str | None
    run_id: ID
    trace_id: str | None
    draft_ref: "tuple[str, int] | None"
    project_id: str


def _execution_inputs(req: ExecutionRequest) -> ExecutionInputs:
    """加载协议/目录/项目并构建命令（override 时 catalog/project 与 preflight 同源）。

    协议来源二选一：旧 `protocol_path`（examples/protocols/ 内）或新
    `draft_ref=(draft_id, revision)`（不可变修订正文；同链 Compile→Preflight→Freeze）。
    WP-B（PLAN-041）：project 设置按路径 project_id 解析（注册项目自动带默认
    设置行；未注册 404——不回退他项目设置，不伪装归属）。
    """
    deps = req.deps
    protocol = _load_protocol_for_run(deps, req.protocol_path, req.draft_ref)
    catalog = merged_catalog_snapshot(deps)
    project = merged_project_settings(deps, req.project_id)
    preflight = deps.preflight_override
    if preflight is not None:
        catalog = preflight.catalog
        project = preflight.project
    else:
        preflight = PreflightContext(
            catalog=catalog,
            project=project,
            credentials=deps.credentials,
            endpoint_health=build_endpoint_health(deps, catalog),
            provider_health=build_provider_health(deps, catalog),
            workspace_available={},
            budget_ledger=deps.budget,
            policy_evaluator=build_policy_evaluator(catalog),
        )
    command = StartRunCommand(
        project_id=project.project_id,
        protocol_id=protocol.id,
        run_id=req.run_id,
        trace_id=req.trace_id or f"api-{req.run_id.value}",
    )
    return ExecutionInputs(protocol, catalog, project, preflight, command)


def _load_protocol_for_run(
    deps: ApiDeps,
    protocol_path: str | None,
    draft_ref: "tuple[str, int] | None",
) -> ProtocolDefinition:
    """协议解析委托 protocol_source 共享实现（path 与草稿修订互斥）。"""
    return load_protocol_for_source(deps, protocol_path, draft_ref)


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
    inputs = _execution_inputs(req)
    run = _run_from_execution(deps, run_id, inputs.project.project_id, inputs.protocol.id, inputs)
    save_run(deps, run)
    return _run_state_dto(deps, run_id.value)


@projects_router.get("/projects/{project_id}/runs", response_model=list[RunDetailDto])
async def list_runs(project_id: str, request: Request) -> list[RunDetailDto]:
    """Run 列表（created_at 倒序；M13-R1 WP-M2：刷新恢复入口）。"""
    scope_project_id = project_id
    deps: ApiDeps = get_deps(request)
    if deps.runs_store is None:
        # 注册表回退（测试注入）同样按项目过滤（WP-B：不跨项目泄漏）。
        return [
            _run_state_dto(deps, run.id.value)
            for run in reversed(list(deps.run_registry.values()))
            if run.project_id == scope_project_id
        ]
    runs = deps.runs_store.list_runs(scope_project_id)
    return [
        RunDetailDto(
            id=run.id.value,
            project_id=run.project_id,
            protocol_id=run.protocol_id,
            state=run.state,
            manifest_digest=str(run.manifest_digest) if run.manifest_digest else None,
            created_at=run.created_at.value.isoformat(),
            updated_at=run.updated_at.value.isoformat(),
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
