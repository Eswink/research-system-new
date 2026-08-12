"""契约加载器公共 API（infrastructure 层）。

按主题拆分实现：
- `base.py`：共享工具（YAML/JSON 读取、schema 校验、扁平化）
- `roles_loaders.py`：Role / Agent / TeamTemplate / Skill
- `models_loaders.py`：LLMEndpoint / ModelDefinition / ModelProfile
- `tasks_loaders.py`：TaskContract / HandoffBundle
"""

from __future__ import annotations

from typing import Any, Callable

from adapters.contracts.base import ContractLoadError, load_yaml
from adapters.contracts.models_loaders import load_llm_endpoints, load_model_profiles, load_models
from adapters.contracts.protocol_loaders import load_protocol
from adapters.contracts.resource_loaders import (
    load_budget_policies,
    load_policy,
    load_project,
    load_tool_providers,
    load_workspaces,
)
from adapters.contracts.roles_loaders import (
    load_agents,
    load_roles,
    load_skills,
    load_team_templates,
)
from adapters.contracts.tasks_loaders import load_handoff_bundles, load_task_contracts

__all__ = [
    "ContractLoadError",
    "load_agents",
    "load_budget_policies",
    "load_collection",
    "load_handoff_bundles",
    "load_llm_endpoints",
    "load_model_profiles",
    "load_models",
    "load_policy",
    "load_project",
    "load_protocol",
    "load_roles",
    "load_skills",
    "load_task_contracts",
    "load_team_templates",
    "load_tool_providers",
    "load_workspaces",
    "load_yaml",
]

_COLLECTION_LOADERS: dict[str, Callable[..., dict[str, Any]]] = {
    "roles": load_roles,
    "agents": load_agents,
    "team_templates": load_team_templates,
    "llm_endpoints": load_llm_endpoints,
    "models": load_models,
    "model_profiles": load_model_profiles,
    "task_contracts": load_task_contracts,
    "budget_policies": load_budget_policies,
    "tool_providers": load_tool_providers,
    "workspaces": load_workspaces,
    "skills": load_skills,
}


def load_collection(kind: str, relative_path: str) -> dict[str, Any]:
    loader = _COLLECTION_LOADERS.get(kind)
    if loader is None:
        raise ContractLoadError(f"unknown contract collection: {kind}")
    return loader(relative_path)
