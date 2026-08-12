"""真实 examples 契约资产的端到端编译/预检集成测试。

用仓库实际配置资产（roles/agents/team_templates/models/profiles/endpoints/
tool_providers/workspaces/budgets/policy/task_contracts/protocol）验证：
- loader 全链可解析；
- 编译器不崩溃并产出结构化阻断 findings（agent 池不足 -> AGENT_MISSING）；
- Preflight 将 compile findings 聚合为 FAIL 报告。
"""

from __future__ import annotations

from adapters.contracts import (
    load_agents,
    load_budget_policies,
    load_llm_endpoints,
    load_model_profiles,
    load_models,
    load_policy,
    load_protocol,
    load_roles,
    load_skills,
    load_task_contracts,
    load_team_templates,
    load_tool_providers,
    load_workspaces,
)
from packages.application import compile_protocol, run_preflight
from packages.application.policy.native import NativePolicyEvaluator
from packages.application.ports import CatalogSnapshot, PreflightContext, ProjectSettings
from packages.domain.enums import EndpointHealth, ReviewPanelRole, WorkspacePolicy
from tests.application.protocol_fixtures import Credentials


def _example_catalog() -> CatalogSnapshot:
    return CatalogSnapshot(
        roles=load_roles("examples/config/roles.yaml"),
        agents=load_agents("examples/config/agents.yaml"),
        team_templates=load_team_templates("examples/config/team_templates.yaml"),
        models=load_models("examples/config/models.yaml"),
        model_profiles=load_model_profiles("examples/config/model_profiles.yaml"),
        task_contracts=load_task_contracts("examples/contracts/task_contracts.yaml"),
        endpoints=load_llm_endpoints("examples/config/llm_endpoints.yaml"),
        tool_providers=load_tool_providers("examples/config/tool_providers.yaml"),
        workspaces=load_workspaces("examples/config/backends.yaml"),
        budget_policies=load_budget_policies("examples/config/budgets.yaml"),
        policy=load_policy("examples/config/policy.yaml"),
        skills=load_skills("examples/config/skills.yaml"),
    )


def _example_project() -> ProjectSettings:
    return ProjectSettings(
        project_id="example-project",
        team_template_id="standard",
        default_model_profile_id="research_strong",
        budget_policy_id="low_cost",
        workspace_backend="openhands_docker",
    )


def test_real_example_assets_compile_to_structured_blocking_findings() -> None:
    protocol = load_protocol("examples/protocols/ai_ml_research_v0_4_0.yaml")
    catalog = _example_catalog()
    project = _example_project()
    policy = catalog.policy
    assert policy is not None
    context = PreflightContext(
        catalog=catalog,
        project=project,
        credentials=Credentials(),
        endpoint_health={eid: EndpointHealth.HEALTHY for eid in catalog.endpoints},
        policy_evaluator=NativePolicyEvaluator(policy),
    )
    result = compile_protocol(protocol, catalog, project)
    # agent 池不足以满足协议全部角色下限 -> 结构化阻断，而不是崩溃
    assert result.plan is not None
    assert "AGENT_MISSING" in {finding.code for finding in result.findings}
    report = run_preflight(result.plan, context, result.findings)
    assert report.status.value == "FAIL"
    # 角色能力面必须闭合：skill 展开的 capability 不得越出 role 请求面
    assert "AGENT_PERMISSION_DENIED" not in {finding.code for finding in report.findings}


def test_example_plan_projects_phase_agent_bindings() -> None:
    protocol = load_protocol("examples/protocols/ai_ml_research_v0_4_0.yaml")
    catalog = _example_catalog()
    project = _example_project()
    result = compile_protocol(protocol, catalog, project)
    assert result.plan is not None
    assignments = {item.phase_id: item for item in result.plan.phase_assignments}
    # domain_discovery 要求 domain_researcher 1..1
    discovery = assignments.get("domain_discovery")
    assert discovery is not None
    assert set(discovery.role_assignments) == {"domain_researcher", "literature_scout"}
    assert discovery.role_assignments["domain_researcher"] == ("domain_a",)
    # 所有分配的 agent 必须已解析模型且角色匹配
    for agent_id in discovery.role_assignments["domain_researcher"]:
        assert agent_id in result.plan.resolved_models


def test_example_catalog_skill_refs_resolve() -> None:
    catalog = _example_catalog()
    # domain_a 声明 evidence_modeling skill，必须已注册
    agent = catalog.agents["domain_a"]
    assert agent.skill_refs == ["evidence_modeling"]
    assert "evidence_modeling" in catalog.skills
    reviewer = catalog.agents["reviewer_a"]
    assert reviewer.skill_refs == ["scientific_review"]
    assert "scientific_review" in catalog.skills


def test_example_writer_and_reviewer_models_are_disjoint() -> None:
    """真实 fixtures 中 writer 与 reviewer 主模型不得共享（HETEROGENEITY_VIOLATION 前置）。"""
    catalog = _example_catalog()
    panel_by_role = {role_id: role.review_panel_role for role_id, role in catalog.roles.items()}

    def _primary_model(agent_id: str) -> str:
        agent = catalog.agents[agent_id]
        binding = agent.model_binding
        if binding.mode.value == "EXPLICIT_MODEL":
            assert binding.value is not None
            return binding.value
        assert binding.value is not None
        return catalog.model_profiles[binding.value].primary

    writer_models = {
        _primary_model(aid)
        for aid, agent in catalog.agents.items()
        if panel_by_role[agent.role] is ReviewPanelRole.WRITER
    }
    reviewer_models = {
        _primary_model(aid)
        for aid, agent in catalog.agents.items()
        if panel_by_role[agent.role] is ReviewPanelRole.REVIEWER
    }
    assert writer_models, "fixture 必须至少有一个 WRITER agent"
    assert reviewer_models, "fixture 必须至少有一个 REVIEWER agent"
    assert not (writer_models & reviewer_models), (
        f"fixture writer/reviewer 模型共享: {sorted(writer_models & reviewer_models)}"
    )


def test_example_engineer_inherits_isolated_writable_workspace() -> None:
    """engineer 未显式配置 workspace_policy → 继承 role 的 isolated_writable。"""
    catalog = _example_catalog()
    agent = catalog.agents["engineer"]
    assert agent.workspace_policy is None
    role = catalog.roles[agent.role]
    assert role.workspace_policy.value == "isolated_writable"


def test_example_agents_workspace_policy_within_role_boundary() -> None:
    """fixtures 中所有显式 workspace_policy 都落在 role 边界内。"""
    catalog = _example_catalog()
    for agent in catalog.agents.values():
        role = catalog.roles[agent.role]
        if agent.workspace_policy is None:
            continue
        allowed = agent.workspace_policy == role.workspace_policy or (
            agent.workspace_policy == WorkspacePolicy.READ_ONLY
        )
        assert allowed, f"agent {agent.id} workspace policy 超出 role {agent.role} 边界"
