"""Control Plane API 契约目录服务：从 examples/ 加载 CatalogSnapshot。

M13 控制面数据源：wizard 阶段使用 examples/config/ 与 examples/protocols/
的正式契约（与 m12_reference_workflow 同源）；M14 PostgreSQL canonical
state 落地后替换为本服务实现（CatalogSnapshot Port 不变）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from adapters.contracts import (
    load_agents,
    load_budget_policies,
    load_llm_endpoints,
    load_model_profiles,
    load_models,
    load_policy,
    load_project,
    load_roles,
    load_skills,
    load_task_contracts,
    load_team_templates,
    load_tool_providers,
    load_workspaces,
)
from adapters.contracts.protocol_loaders import load_protocol
from packages.application.ports import CatalogSnapshot, ProjectSettings

_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_DIR = "examples/config"
_PROTOCOLS_DIR = "examples/protocols"
_CONTRACTS_DIR = "examples/contracts"


def load_catalog_snapshot() -> CatalogSnapshot:
    """加载完整目录快照（roles/agents/templates/models/profiles/...）。"""
    return CatalogSnapshot(
        roles=load_roles(f"{_CONFIG_DIR}/roles.yaml"),
        agents=load_agents(f"{_CONFIG_DIR}/agents.yaml"),
        team_templates=load_team_templates(f"{_CONFIG_DIR}/team_templates.yaml"),
        models=load_models(f"{_CONFIG_DIR}/models.yaml"),
        model_profiles=load_model_profiles(f"{_CONFIG_DIR}/model_profiles.yaml"),
        task_contracts=load_task_contracts(f"{_CONTRACTS_DIR}/task_contracts.yaml"),
        endpoints=load_llm_endpoints(f"{_CONFIG_DIR}/llm_endpoints.yaml"),
        tool_providers=load_tool_providers(f"{_CONFIG_DIR}/tool_providers.yaml"),
        workspaces=load_workspaces(f"{_CONFIG_DIR}/backends.yaml"),
        budget_policies=load_budget_policies(f"{_CONFIG_DIR}/budgets.yaml"),
        skills=load_skills(f"{_CONFIG_DIR}/skills.yaml"),
        policy=load_policy(f"{_CONFIG_DIR}/policy.yaml"),
        # 如实：example providers 未登记 pin → preflight SUPPLY_CHAIN_UNPINNED
        # 如实暴露（AGENTS.md §9 unpinned plugin 默认 deny）；受控 E2E 由
        # 测试夹具显式注入 pin 后走 freeze happy path。
        tool_pack_digests={},
    )


def load_project_settings() -> ProjectSettings:
    """加载示例项目设置（wizard 默认项目；M14 后替换为持久化项目）。"""
    body = load_project(f"{_CONFIG_DIR}/project.yaml")
    return ProjectSettings(
        project_id="example-project",
        team_template_id=str(body["team_template"]),
        default_model_profile_id=(
            str(body["default_model_profile"]) if body.get("default_model_profile") else None
        ),
        budget_policy_id=str(body["budget"]),
        workspace_backend=str(body["workspace_backend"]),
        compute_profile=None,
        policy_id=str(body.get("policy", "project-policy")),
    )


def load_protocol_definition(path: str) -> Any:
    """加载协议定义（examples/protocols/ 内路径，禁止路径穿越）。"""
    resolved = (_ROOT / _PROTOCOLS_DIR / path).resolve()
    root = (_ROOT / _PROTOCOLS_DIR).resolve()
    if not str(resolved).startswith(str(root)) or resolved.suffix != ".yaml":
        raise ValueError(f"protocol path must be within {_PROTOCOLS_DIR}: {path!r}")
    if not resolved.is_file():
        raise ValueError(f"protocol file not found: {path!r}")
    return load_protocol(f"{_PROTOCOLS_DIR}/{path}")
