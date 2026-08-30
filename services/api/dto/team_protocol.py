"""Team / Protocol / Preflight / Dry-run DTO。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RoleDefinitionDto(BaseModel):
    """RoleDefinition 视图（不绑定模型；ADR-0011）。"""

    id: str
    role_type: str
    category: str
    activation_default: str
    requested_capabilities: list[str] = Field(default_factory=list)
    hard_model_capabilities: dict[str, list[str]] = Field(default_factory=dict)
    default_model_profile: str | None = None
    workspace_policy: str = "read_only"
    default_skills: list[str] = Field(default_factory=list)
    review_panel_role: str = "NONE"


class TeamTemplateDto(BaseModel):
    """Lean / Standard / Rigorous 模板视图。"""

    id: str
    display_name: str
    extends: str | None = None
    roles: dict[str, dict[str, int]] = Field(default_factory=dict)


class AgentSpecDto(BaseModel):
    """AgentSpec 实例（Role 的配置实例；可独立绑定模型）。"""

    id: str
    role: str
    model_binding: dict[str, str | None] = Field(default_factory=dict)
    workspace_policy: str | None = None
    skill_refs: list[str] = Field(default_factory=list)
    capability_refs: list[str] = Field(default_factory=list)
    max_context_tokens: int | None = None
    max_iterations: int | None = None
    runtime_kind: str | None = None
    budget_policy_ref: str | None = None
    version: str = Field(default="", description="resource version（ETag 值，If-Match 用）")


class AgentCreateDto(BaseModel):
    """创建 Agent 实例（Role 的配置实例；同 Role 可多实例）。"""

    role: str = Field(min_length=1, max_length=200)
    model_binding: dict[str, str | None] = Field(default_factory=dict)
    workspace_policy: str | None = None
    max_context_tokens: int | None = Field(default=None, ge=1)
    max_iterations: int | None = Field(default=None, ge=1)


class AgentUpdateDto(BaseModel):
    """per-Agent ModelBinding 更新（semantic 变更走 Manifest Revision/Fork）。"""

    model_binding: dict[str, str | None] | None = None
    workspace_policy: str | None = None
    max_context_tokens: int | None = None
    max_iterations: int | None = None


class ProjectSettingsUpdateDto(BaseModel):
    """项目设置保存（全量显式；template/workspace 引用由服务端校验）。"""

    team_template_id: str = Field(min_length=1, max_length=200)
    default_model_profile_id: str | None = Field(default=None, max_length=200)
    budget_policy_id: str = Field(min_length=1, max_length=200)
    workspace_backend: str = Field(min_length=1, max_length=200)
    compute_profile: str | None = Field(default=None, max_length=200)
    policy_id: str = Field(default="project-policy", min_length=1, max_length=200)


class ProjectSettingsDto(BaseModel):
    project_id: str
    team_template_id: str
    default_model_profile_id: str | None = None
    budget_policy_id: str
    workspace_backend: str
    compute_profile: str | None = None
    policy_id: str = "project-policy"


class ProtocolSourceDto(BaseModel):
    """协议文件路径（examples/protocols/ 内，wizard 选择）。"""

    path: str = Field(min_length=1, max_length=500)


class CompileResultDto(BaseModel):
    plan_id: str | None = None
    protocol_digest: str | None = None
    findings: list[dict[str, object]] = Field(default_factory=list)
    successful: bool


class PreflightReportDto(BaseModel):
    status: str
    findings: list[dict[str, object]] = Field(default_factory=list)
    estimated_cost: float | None = None
    estimated_cost_currency: str | None = None
    reserved_budget_ref: str | None = None
    unresolved_risks: list[str] = Field(default_factory=list)


class DryRunProjectionDto(BaseModel):
    role_counts: dict[str, int] = Field(default_factory=dict)
    agent_models: dict[str, str] = Field(default_factory=dict)
    tools: dict[str, list[str]] = Field(default_factory=dict)
    workspaces: dict[str, str] = Field(default_factory=dict)
    compute_profiles: dict[str, str | None] = Field(default_factory=dict)
    budget_reservations: list[dict[str, object]] = Field(default_factory=list)
    estimated_cost_minor: int | None = None
    estimated_cost_currency: str | None = None
    approval_actions: list[str] = Field(default_factory=list)
