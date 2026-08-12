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
    load_task_contracts,
    load_team_templates,
    load_tool_providers,
    load_workspaces,
)
from packages.application import compile_protocol, run_preflight
from packages.application.protocol_compile import CatalogSnapshot, PreflightContext, ProjectSettings
from packages.domain.enums import EndpointHealth
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
    context = PreflightContext(
        catalog=catalog,
        project=project,
        credentials=Credentials(),
        endpoint_health={eid: EndpointHealth.HEALTHY for eid in catalog.endpoints},
    )
    result = compile_protocol(protocol, catalog, project)
    # agent 池不足以满足协议全部角色下限 -> 结构化阻断，而不是崩溃
    assert result.plan is not None
    assert "AGENT_MISSING" in {finding.code for finding in result.findings}
    report = run_preflight(result.plan, context, result.findings)
    assert report.status.value == "FAIL"
