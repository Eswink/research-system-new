"""Control Plane API 契约目录服务：从 examples/ 加载 CatalogSnapshot。

M13 控制面数据源：wizard 阶段使用 examples/config/ 与 examples/protocols/
的正式契约（与 m12_reference_workflow 同源）；M14 PostgreSQL canonical
state 落地后替换为本服务实现（CatalogSnapshot Port 不变）。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

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
from packages.domain.policy import PolicyDefinition

_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_DIR = "examples/config"
_PROTOCOLS_DIR = "examples/protocols"
_CONTRACTS_DIR = "examples/contracts"


def load_policy_definition() -> PolicyDefinition | None:
    """项目策略定义（examples/config/policy.yaml）。

    控制面运行时策略面（记忆门链等）与控制面可见性（GET /policy/capabilities）
    共用同一份策略；文件缺失或不可解析时返回 None —— 调用方必须按诚实缺口
    处理（503/显式 None），不得伪造默认策略。
    """
    try:
        return load_policy(f"{_CONFIG_DIR}/policy.yaml")
    except (OSError, ValueError):
        return None


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
        # M13-R1: toolpack 契约目录中的已 pin digest 如实接入（与 M12 参考
        # 流程同源逻辑，不新造校验规则）；未被 pin 的 provider 仍由 preflight
        # SUPPLY_CHAIN_UNPINNED 如实暴露（默认 deny 语义保持）。
        tool_pack_digests=_load_tool_pack_digests(),
    )


def _load_tool_pack_digests() -> dict[str, str]:
    """读取 examples/contracts/toolpack_*.yaml 的 pinned digest（provider_id -> digest）。

    与 m12_reference_workflow 的 _tool_pack_digests 同源逻辑；
    toolpack_manifest.yaml 是 schema 规格，不是真实 pack，跳过。
    """
    contracts_root = _ROOT / _CONTRACTS_DIR
    result: dict[str, str] = {}
    for path in sorted(contracts_root.glob("toolpack_*.yaml")):
        if path.stem == "toolpack_manifest":
            continue
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        digest = payload.get("digest") if isinstance(payload, dict) else None
        provider_id = str(payload.get("id", "")) if isinstance(payload, dict) else ""
        provider_id = re.sub(r"_v\d+(\.\d+)*$", "", provider_id)
        if isinstance(digest, str) and digest and provider_id:
            result[provider_id] = digest
    return result


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
        reference_protocol=_reference_protocol(body.get("protocol")),
    )


def load_project_name(project_id: str = "example-project") -> str:
    """项目显示名（examples 契约 project.name；PLAN-041 注册表默认条目用）。"""
    body = load_project(f"{_CONFIG_DIR}/project.yaml")
    name = str(body.get("name") or "").strip()
    return name or project_id


def _reference_protocol(raw_protocol: object) -> str | None:
    """project.yaml protocol → examples/protocols 文件名（WP-C）。

    存储形态统一为带 `.yaml` 后缀的文件名；未配置返回 None（诚实空态）。
    """
    if raw_protocol is None or not str(raw_protocol).strip():
        return None
    name = str(raw_protocol).strip()
    return name if name.endswith(".yaml") else f"{name}.yaml"


def load_protocol_definition(path: str) -> Any:
    """加载协议定义（examples/protocols/ 内路径，禁止路径穿越）。"""
    resolved = (_ROOT / _PROTOCOLS_DIR / path).resolve()
    root = (_ROOT / _PROTOCOLS_DIR).resolve()
    if not str(resolved).startswith(str(root)) or resolved.suffix != ".yaml":
        raise ValueError(f"protocol path must be within {_PROTOCOLS_DIR}: {path!r}")
    if not resolved.is_file():
        raise ValueError(f"protocol file not found: {path!r}")
    return load_protocol(f"{_PROTOCOLS_DIR}/{path}")
