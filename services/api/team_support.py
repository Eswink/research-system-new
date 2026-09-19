"""Team 路由共享支持（M13-R1：team_protocol.py 300 行阈值拆分）。

承担：preflight context 构造、协议编译、Agent DTO→Domain 转换与
引用校验。这些是路由层编排辅助，不含业务规则（业务规则在
packages.application.preflight / domain）。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.ports import (
    AgentStore,
    CatalogSnapshot,
    PreflightContext,
    ProjectSettings,
)
from packages.application.protocol_compile.compiler import compile_protocol
from packages.domain.enums import BackendKind, ModelBindingMode, WorkspacePolicy
from packages.domain.protocols import CompiledRunPlan, ProtocolDefinition
from packages.domain.roles import AgentBinding, AgentContextConfig, AgentSpec
from services.api.catalog_merge import merged_catalog_snapshot, merged_project_settings
from services.api.composition import ApiDeps
from services.api.errors import ApiError
from services.api.preflight_support import (
    build_endpoint_health,
    build_endpoint_url_denials,
    build_policy_evaluator,
    build_provider_health,
    runtime_fingerprints,
    runtime_substrate,
)


def build_preflight_context(
    deps: ApiDeps,
    catalog: CatalogSnapshot,
    project: ProjectSettings,
) -> PreflightContext:
    """preflight context：真实 credential/health/policy 接线（B3.3/B3.4）。"""
    return PreflightContext(
        catalog=catalog,
        project=project,
        credentials=deps.credentials,
        endpoint_health=build_endpoint_health(deps, catalog),
        endpoint_url_denials=build_endpoint_url_denials(deps, catalog),
        provider_health=build_provider_health(deps, catalog),
        workspace_available={},
        budget_ledger=None,
        policy_evaluator=build_policy_evaluator(catalog),
        execution_substrate=runtime_substrate(deps),
        runtime_fingerprints=runtime_fingerprints(deps),
    )


def compile_plan_for_protocol(
    deps: ApiDeps, protocol: ProtocolDefinition, project_id: str = "example-project"
) -> CompiledRunPlan:
    """编译已加载的 ProtocolDefinition（path 或草稿修订同源；WP-B）。"""
    catalog = merged_catalog_snapshot(deps)
    project = merged_project_settings(deps, project_id)
    result = compile_protocol(protocol, catalog, project)
    if result.plan is None:
        raise ApiError(
            422,
            "Protocol Compile Failed",
            "; ".join(finding.message for finding in result.findings),
        )
    return result.plan


def merged_context(
    deps: ApiDeps, project_id: str = "example-project"
) -> tuple[CatalogSnapshot, ProjectSettings]:
    """合并目录 + 合并项目设置的便捷二元组（WP-B：project 归属贯通）。"""
    return merged_catalog_snapshot(deps), merged_project_settings(deps, project_id)


@dataclass(frozen=True, slots=True)
class AgentDraft:
    """Agent 创建/更新的可编辑字段（参数对象，规避参数爆发）。"""

    agent_id: str
    role: str
    binding: AgentBinding
    workspace_policy: str | None = None
    max_context_tokens: int | None = None
    max_iterations: int | None = None


def binding_from_dto(model_binding: dict[str, str | None] | None) -> AgentBinding:
    """DTO model_binding → domain AgentBinding（非法模式/值 → 422）。"""
    raw = model_binding or {}
    try:
        mode = ModelBindingMode(raw.get("mode") or "INHERIT")
    except ValueError as exc:
        raise ApiError(
            422, "Invalid Binding", f"unknown binding mode: {raw.get('mode')!r}"
        ) from exc
    try:
        return AgentBinding(mode=mode, value=raw.get("value"))
    except ValueError as exc:
        raise ApiError(422, "Invalid Binding", str(exc)) from exc


def validate_model_reference(catalog: CatalogSnapshot, binding: AgentBinding) -> None:
    """模型/模型画像引用必须解析于合并目录（后端校验，不依赖 UI 隐藏）。"""
    if binding.mode is ModelBindingMode.INHERIT:
        return
    if binding.mode is ModelBindingMode.EXPLICIT_MODEL:
        owned = set(catalog.models)
        label = "model"
    else:
        owned = set(catalog.model_profiles)
        label = "model profile"
    if binding.value not in owned:
        raise ApiError(422, "Invalid Binding", f"{label} is unavailable: {binding.value!r}")


def agent_from_dto(draft: AgentDraft, base: AgentSpec | None = None) -> AgentSpec:
    """DTO → AgentSpec（role/model 引用校验前置，避免损坏配置写入）。"""
    policy: WorkspacePolicy | None = None
    if draft.workspace_policy is not None:
        try:
            policy = WorkspacePolicy(draft.workspace_policy)
        except ValueError as exc:
            raise ApiError(
                422,
                "Invalid Workspace Policy",
                f"unknown workspace policy: {draft.workspace_policy!r}",
            ) from exc
    return AgentSpec(
        id=draft.agent_id,
        role=draft.role,
        model_binding=draft.binding,
        workspace_policy=policy,
        skill_refs=list(base.skill_refs if base else []),
        capability_refs=list(base.capability_refs if base else []),
        context=AgentContextConfig(
            max_context_tokens=draft.max_context_tokens,
            max_iterations=draft.max_iterations,
        ),
        runtime_kind=base.runtime_kind if base else BackendKind.OPENHANDS_NATIVE,
        budget_policy_ref=base.budget_policy_ref if base else None,
    )


def require_agent_store(deps: ApiDeps) -> AgentStore:
    if deps.agent_store is None:
        raise ApiError(503, "Agent Store Unavailable", "agent store not configured")
    return deps.agent_store
