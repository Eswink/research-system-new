"""Role / Team / Agent 域实体定义。

来源：docs/architecture/ROLE_MODEL.md、schemas/role-definition.schema.json、
schemas/agent-spec.schema.json、schemas/team-template.schema.json。
Role 不绑定具体 ModelDefinition（ADR-0011）。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from packages.domain.enums import (
    ActivationPolicy,
    BackendKind,
    ModelBindingMode,
    ReviewPanelRole,
    RoleCategory,
    SelectionStrategy,
    WorkspacePolicy,
)


@dataclass(frozen=True, slots=True)
class ModelCapabilityRequirement:
    all_of: list[str] = field(default_factory=list)
    any_of: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class RoleDefinition:
    id: str
    role_type: str
    category: RoleCategory
    activation_default: ActivationPolicy
    requested_capabilities: list[str] = field(default_factory=list)
    hard_model_capabilities: ModelCapabilityRequirement = field(
        default_factory=ModelCapabilityRequirement
    )
    default_model_profile: str | None = None
    workspace_policy: WorkspacePolicy = WorkspacePolicy.READ_ONLY
    default_skills: list[str] = field(default_factory=list)
    forbidden_capabilities: list[str] = field(default_factory=list)
    review_panel_role: ReviewPanelRole = ReviewPanelRole.NONE

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("role id must not be empty")
        if not self.role_type:
            raise ValueError("role type must not be empty")
        denied = set(self.requested_capabilities) & set(self.forbidden_capabilities)
        if denied:
            raise ValueError(
                f"role {self.id} requests and forbids the same capability: {sorted(denied)}"
            )


@dataclass(frozen=True, slots=True)
class AgentBinding:
    mode: ModelBindingMode
    value: str | None = None

    def __post_init__(self) -> None:
        if self.mode is ModelBindingMode.INHERIT:
            if self.value is not None:
                raise ValueError("INHERIT binding must not carry a value")
        elif self.value is None:
            raise ValueError(f"{self.mode.value} binding requires a value")


@dataclass(frozen=True, slots=True)
class AgentContextConfig:
    """Agent 会话上下文配置面（M4 仅配置契约，运行时执行在 M6/M7）。"""

    max_context_tokens: int | None = None
    max_iterations: int | None = None

    def __post_init__(self) -> None:
        if self.max_context_tokens is not None and self.max_context_tokens < 1:
            raise ValueError("max_context_tokens must be >= 1")
        if self.max_iterations is not None and self.max_iterations < 1:
            raise ValueError("max_iterations must be >= 1")


@dataclass(frozen=True, slots=True)
class AgentSpec:
    id: str
    role: str
    model_binding: AgentBinding
    workspace_policy: WorkspacePolicy | None = None
    skill_refs: list[str] = field(default_factory=list)
    capability_refs: list[str] = field(default_factory=list)
    context: AgentContextConfig | None = None
    runtime_kind: BackendKind | None = None
    budget_policy_ref: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("agent id must not be empty")
        if not self.role:
            raise ValueError("agent role must not be empty")


@dataclass(frozen=True, slots=True)
class RolePool:
    min_instances: int
    max_instances: int
    concurrency: int = 1
    selection_strategy: SelectionStrategy = SelectionStrategy.FIXED
    model_profile: str | None = None
    activation_policy: ActivationPolicy | None = None

    def __post_init__(self) -> None:
        if self.min_instances < 0:
            raise ValueError("min_instances must be non-negative")
        if self.max_instances < self.min_instances:
            raise ValueError("max_instances must be >= min_instances")
        if self.concurrency < 1:
            raise ValueError("concurrency must be >= 1")


@dataclass(frozen=True, slots=True)
class TeamTemplate:
    id: str
    display_name: str
    roles: dict[str, RolePool] = field(default_factory=dict)
    extends: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("team template id must not be empty")
        if not self.roles:
            raise ValueError("team template must declare at least one role pool")
