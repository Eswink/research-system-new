"""M4：写面 capability 与 agent 有效 workspace policy 的静态一致性检查测试。

一致性语义：workspace.write.code / workspace.delete 需要 isolated_writable；
deliverable.write / deliverable.edit 需要 deliverable_only 或 isolated_writable；
workspace.write.notes 需要 notes_only 或 isolated_writable。
M6/M7 执行期 Policy Wrapper 负责运行时 enforce，本检查在 preflight 静态拒绝明显不一致配置。
"""

from __future__ import annotations

from dataclasses import replace

from packages.application.ports import CatalogSnapshot
from packages.application.preflight.preflight import compile_and_preflight
from packages.application.preflight.role_checks import check_agent_permissions
from packages.application.protocol_compile import compile_protocol
from packages.domain.core import Version
from packages.domain.enums import (
    ActivationPolicy,
    ModelBindingMode,
    RoleCategory,
    WorkspacePolicy,
)
from packages.domain.protocols import (
    PhaseStrategy,
    ProtocolDefinition,
    ProtocolPhase,
    RoleRequirement,
)
from packages.domain.roles import AgentBinding, AgentSpec, RoleDefinition
from tests.application import protocol_fixtures as fixtures


def _protocol() -> ProtocolDefinition:
    return ProtocolDefinition(
        id="m4_workspace_capability_v0_4_0",
        version=Version("0.4.0"),
        phases=[
            ProtocolPhase(
                id="collect",
                strategy=PhaseStrategy.PARALLEL_AGENTS,
                required_roles=[RoleRequirement("researcher", 1, 1)],
                required_capabilities=["literature.search"],
            )
        ],
    )


def _role(
    *,
    workspace_policy: WorkspacePolicy,
    capabilities: list[str],
) -> RoleDefinition:
    return RoleDefinition(
        id="researcher",
        role_type="Researcher",
        category=RoleCategory.DISCOVERY,
        activation_default=ActivationPolicy.REQUIRED_BY_PROTOCOL,
        requested_capabilities=capabilities,
        workspace_policy=workspace_policy,
    )


def _agent(
    *,
    workspace_policy: WorkspacePolicy | None,
    capability_refs: list[str],
) -> AgentSpec:
    return AgentSpec(
        id="agent-1",
        role="researcher",
        model_binding=AgentBinding(mode=ModelBindingMode.EXPLICIT_MODEL, value="model-1"),
        workspace_policy=workspace_policy,
        capability_refs=capability_refs,
    )


def _catalog(role: RoleDefinition, agent: AgentSpec) -> CatalogSnapshot:
    return replace(
        fixtures.catalog(),
        roles={"researcher": role},
        agents={"agent-1": agent},
    )


def _findings(role: RoleDefinition, agent: AgentSpec) -> list[str]:
    catalog = _catalog(role, agent)
    result = compile_protocol(_protocol(), catalog, fixtures.context().project)
    assert result.plan is not None
    return [
        finding.code for finding in check_agent_permissions(result.plan, fixtures.context(catalog))
    ]


def test_read_only_agent_rejects_workspace_write_code() -> None:
    role = _role(workspace_policy=WorkspacePolicy.READ_ONLY, capabilities=["workspace.write.code"])
    agent = _agent(
        workspace_policy=WorkspacePolicy.READ_ONLY,
        capability_refs=["workspace.write.code"],
    )
    assert "WORKSPACE_POLICY_VIOLATION" in _findings(role, agent)


def test_notes_only_agent_rejects_workspace_write_code() -> None:
    role = _role(workspace_policy=WorkspacePolicy.NOTES_ONLY, capabilities=["workspace.write.code"])
    agent = _agent(
        workspace_policy=WorkspacePolicy.NOTES_ONLY,
        capability_refs=["workspace.write.code"],
    )
    assert "WORKSPACE_POLICY_VIOLATION" in _findings(role, agent)


def test_notes_only_agent_allows_workspace_write_notes() -> None:
    role = _role(
        workspace_policy=WorkspacePolicy.NOTES_ONLY,
        capabilities=["workspace.write.notes"],
    )
    agent = _agent(
        workspace_policy=WorkspacePolicy.NOTES_ONLY,
        capability_refs=["workspace.write.notes"],
    )
    assert _findings(role, agent) == []


def test_deliverable_only_agent_allows_deliverable_write() -> None:
    role = _role(
        workspace_policy=WorkspacePolicy.DELIVERABLE_ONLY,
        capabilities=["deliverable.write"],
    )
    agent = _agent(
        workspace_policy=WorkspacePolicy.DELIVERABLE_ONLY,
        capability_refs=["deliverable.write"],
    )
    assert _findings(role, agent) == []


def test_isolated_writable_agent_allows_all_write_surfaces() -> None:
    capabilities = [
        "workspace.write.notes",
        "workspace.write.code",
        "workspace.delete",
        "deliverable.write",
        "deliverable.edit",
    ]
    role = _role(workspace_policy=WorkspacePolicy.ISOLATED_WRITABLE, capabilities=capabilities)
    agent = _agent(
        workspace_policy=WorkspacePolicy.ISOLATED_WRITABLE,
        capability_refs=capabilities,
    )
    assert _findings(role, agent) == []


def test_read_only_agent_inheriting_role_policy_rejects_deliverable_write() -> None:
    # agent 未显式配置 workspace_policy → 继承 role 的 read_only
    role = _role(workspace_policy=WorkspacePolicy.READ_ONLY, capabilities=["deliverable.write"])
    agent = _agent(
        workspace_policy=None,
        capability_refs=["deliverable.write"],
    )
    assert "WORKSPACE_POLICY_VIOLATION" in _findings(role, agent)


def test_capability_workspace_mismatch_blocks_preflight() -> None:
    role = _role(workspace_policy=WorkspacePolicy.READ_ONLY, capabilities=["workspace.write.code"])
    agent = _agent(
        workspace_policy=WorkspacePolicy.READ_ONLY,
        capability_refs=["workspace.write.code"],
    )
    catalog = _catalog(role, agent)
    plan, report = compile_and_preflight(
        _protocol(),
        catalog,
        fixtures.context().project,
        fixtures.context(catalog),
    )
    assert plan is not None
    assert report.status.value == "FAIL"
    assert "WORKSPACE_POLICY_VIOLATION" in {finding.code for finding in report.findings}
