"""ResourceCatalog Port 与 Preflight 上下文 DTO。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Protocol, runtime_checkable

from packages.application.ports.budget_ledger import BudgetLedger
from packages.application.ports.credential_resolver import CredentialResolver
from packages.application.ports.policy_evaluator import PolicyEvaluator
from packages.domain.budget import BudgetPolicy
from packages.domain.enums import EndpointHealth
from packages.domain.models import LLMEndpoint, ModelDefinition, ModelProfile
from packages.domain.policy import PolicyDefinition
from packages.domain.roles import AgentSpec, RoleDefinition, TeamTemplate
from packages.domain.tasks import TaskContract
from packages.domain.tools import SkillSpec, ToolProviderSpec
from packages.domain.workspace import Workspace


@dataclass(frozen=True, slots=True)
class ProjectSettings:
    project_id: str
    team_template_id: str
    default_model_profile_id: str | None
    budget_policy_id: str
    workspace_backend: str
    compute_profile: str | None = None
    policy_id: str = "project-policy"
    # WP-C（PLAN-040）：项目参考协议（examples/protocols 内文件名的受控模板
    # 引用；Team 页预检用它，不再由前端硬编码 demo 协议）。None = 未配置。
    reference_protocol: str | None = None

    def __post_init__(self) -> None:
        if not self.project_id:
            raise ValueError("project_id must not be empty")
        if not self.team_template_id:
            raise ValueError("team_template_id must not be empty")
        if not self.budget_policy_id:
            raise ValueError("budget_policy_id must not be empty")
        if not self.workspace_backend:
            raise ValueError("workspace_backend must not be empty")

    @classmethod
    def from_mapping(cls, project_id: str, raw: Mapping[str, object]) -> ProjectSettings:
        return cls(
            project_id=project_id,
            team_template_id=str(raw["team_template"]),
            default_model_profile_id=(
                str(raw["default_model_profile"]) if raw.get("default_model_profile") else None
            ),
            budget_policy_id=str(raw["budget"]),
            workspace_backend=str(raw["workspace_backend"]),
            compute_profile=(str(raw["compute_profile"]) if raw.get("compute_profile") else None),
            policy_id=str(raw.get("policy", "project-policy")),
            reference_protocol=(str(raw["protocol"]) if raw.get("protocol") else None),
        )


@dataclass(frozen=True, slots=True)
class CatalogSnapshot:
    roles: Mapping[str, RoleDefinition] = field(default_factory=dict)
    agents: Mapping[str, AgentSpec] = field(default_factory=dict)
    team_templates: Mapping[str, TeamTemplate] = field(default_factory=dict)
    models: Mapping[str, ModelDefinition] = field(default_factory=dict)
    model_profiles: Mapping[str, ModelProfile] = field(default_factory=dict)
    task_contracts: Mapping[str, TaskContract] = field(default_factory=dict)
    endpoints: Mapping[str, LLMEndpoint] = field(default_factory=dict)
    tool_providers: Mapping[str, ToolProviderSpec] = field(default_factory=dict)
    workspaces: Mapping[str, Workspace] = field(default_factory=dict)
    tool_pack_digests: Mapping[str, str] = field(default_factory=dict)
    budget_policies: Mapping[str, BudgetPolicy] = field(default_factory=dict)
    skills: Mapping[str, SkillSpec] = field(default_factory=dict)
    policy: PolicyDefinition | None = None


@runtime_checkable
class ResourceCatalog(Protocol):
    def snapshot(self) -> CatalogSnapshot: ...


@dataclass(frozen=True, slots=True)
class PreflightContext:
    catalog: CatalogSnapshot
    project: ProjectSettings
    credentials: CredentialResolver | None = None
    endpoint_health: Mapping[str, EndpointHealth] = field(default_factory=dict)
    # WP-D：provider 健康为三态枚举（HEALTHY/DEGRADED/UNKNOWN/OPEN_CIRCUIT/DISABLED）。
    # 控制面 builder 总是对目录内 provider 注入显式值；未注入 key 视为
    # 注入方（单测/fixture）未声明健康面，按 HEALTHY 处理。
    provider_health: Mapping[str, EndpointHealth] = field(default_factory=dict)
    workspace_available: Mapping[str, bool] = field(default_factory=dict)
    budget_ledger: BudgetLedger | None = None
    policy_evaluator: PolicyEvaluator | None = None
