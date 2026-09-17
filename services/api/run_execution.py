"""Run 启动装配（HTTP 面与队列派发器共用）。

`POST /projects/{id}/runs` 与 G14 队列派发器必须走**同一条**装配链：协议来源
解析（路径或草稿修订）→ 目录/项目合并 → preflight 上下文 → `StartRunCommand`
→ `RunOrchestrationService.start_run`。把这段从路由模块抽出来，是为了让队列
派发复用同一实现而不是复制一份"简化版启动"（第二套启动路径 = 第二套语义）。

非职责：不做 HTTP 映射（DTO/异常在 `services/api/routers/runs.py`），不决定
何时启动（派发策略在 `services/api/experiment_queue.py`）。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.ports import CatalogSnapshot, PreflightContext, ProjectSettings
from packages.application.run_orchestration.commands import StartRunCommand
from packages.domain.core import ID, Digest
from packages.domain.protocol_source import ProtocolBody
from packages.domain.protocols import ProtocolDefinition
from packages.domain.run import ResearchRun
from services.api.catalog_merge import merged_catalog_snapshot, merged_project_settings
from services.api.composition import ApiDeps
from services.api.errors import ApiError
from services.api.preflight_support import (
    build_endpoint_health,
    build_policy_evaluator,
    build_provider_health,
)
from services.api.protocol_source import (
    load_protocol_with_body,
    parse_frozen_protocol,
    protocol_source_of,
)
from services.api.routers.run_events import events_of


@dataclass(frozen=True, slots=True)
class ExecutionInputs:
    """start_run 执行输入聚合（参数对象，规避参数爆发）。"""

    protocol: ProtocolDefinition
    catalog: CatalogSnapshot
    project: ProjectSettings
    preflight: PreflightContext
    command: StartRunCommand
    # GOAL-004 cycle 1：被解析的那份协议正文（随 run 落 canonical，供重启重建）。
    protocol_body: ProtocolBody | None = None


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    """start_run 输入参数对象（规避参数爆发）。"""

    deps: ApiDeps
    protocol_path: str | None
    run_id: ID
    trace_id: str | None
    draft_ref: "tuple[str, int] | None"
    project_id: str
    # GOAL-004 cycle 1：冻结正文（有它就不读文件/草稿库；重建路径走这一支）。
    protocol_body: ProtocolBody | None = None


def frozen_manifest_refs_of(
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


def execution_inputs(req: ExecutionRequest) -> ExecutionInputs:
    """加载协议/目录/项目并构建命令（override 时 catalog/project 与 preflight 同源）。

    协议来源二选一：旧 `protocol_path`（examples/protocols/ 内）或新
    `draft_ref=(draft_id, revision)`（不可变修订正文；同链 Compile→Preflight→Freeze）。
    WP-B（PLAN-041）：project 设置按路径 project_id 解析（注册项目自动带默认
    设置行；未注册 404——不回退他项目设置，不伪装归属）。
    """
    deps = req.deps
    if req.protocol_body is not None:
        # 冻结正文优先（GOAL-004 cycle 1）：重建不再依赖那份外部文件还在。
        # 来源参数可有可无——重建只认正文（命令里的来源仅用于记账，缺省不改 run 行）。
        protocol = parse_frozen_protocol(req.protocol_body)
        protocol_body = req.protocol_body
        source = (
            protocol_source_of(req.protocol_path, req.draft_ref)
            if (req.protocol_path or req.draft_ref)
            else None
        )
    else:
        protocol, protocol_body = load_protocol_with_body(deps, req.protocol_path, req.draft_ref)
        source = protocol_source_of(req.protocol_path, req.draft_ref)
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
        protocol_source=source,
        protocol_body=protocol_body,
    )
    return ExecutionInputs(protocol, catalog, project, preflight, command, protocol_body)


def run_from_execution(
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
            # cycle 20：语义 digest 与装配来源都必须过 HTTP 边界——前者是 resume 的
            # 漂移校验输入，后者是重启后重建上下文的唯一入口（丢了就没有续跑入口）。
            manifest_semantic_digest=Digest.parse(outcome.manifest_semantic_digest)
            if outcome.manifest_semantic_digest
            else None,
            pricing_version=outcome.pricing_version,
            pricing_digest=outcome.pricing_digest,
            protocol_source=inputs.command.protocol_source,
            protocol_body=inputs.protocol_body,
        )
    except ValueError:
        frozen_digest, pricing_version, pricing_digest = frozen_manifest_refs_of(deps, run_id.value)
        return ResearchRun(
            id=run_id,
            project_id=project_id,
            protocol_id=protocol_id,
            state="FAILED",
            manifest_digest=Digest.parse(frozen_digest) if frozen_digest else None,
            pricing_version=pricing_version,
            pricing_digest=pricing_digest,
            protocol_source=inputs.command.protocol_source,
            protocol_body=inputs.protocol_body,
        )


def start_run_from_source(req: ExecutionRequest) -> ResearchRun:
    """按协议来源启动一次 run（HTTP 面与队列派发的唯一入口）。

    调用方负责把返回的 run 持久化（`run_access.save_run`）——与 HTTP 面同侧，
    避免出现第二个"只启动了但没登记"的路径。
    """
    inputs = execution_inputs(req)
    return run_from_execution(
        req.deps, req.run_id, inputs.project.project_id, inputs.protocol.id, inputs
    )


__all__ = [
    "ExecutionInputs",
    "ExecutionRequest",
    "execution_inputs",
    "frozen_manifest_refs_of",
    "run_from_execution",
    "start_run_from_source",
]
