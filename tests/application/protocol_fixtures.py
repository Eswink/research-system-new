"""Protocol Compiler 测试所需的最小离线资源目录。"""

from __future__ import annotations

from packages.application.policy.native import NativePolicyEvaluator
from packages.application.ports import SecretValue
from packages.application.protocol_compile import (
    CatalogSnapshot,
    PreflightContext,
    ProjectSettings,
    compile_protocol,
)
from packages.domain.budget import BudgetPolicy
from packages.domain.core import Version
from packages.domain.enums import (
    AcceptanceCriterionType,
    ActivationPolicy,
    CapabilitySource,
    CapabilityStatus,
    EffectClass,
    EndpointHealth,
    ModelBindingMode,
    ModelCapability,
    PolicyDecision,
    ProviderType,
    RoleCategory,
    TrustLevel,
    TrustProfile,
)
from packages.domain.models import CapabilityAssertion, LLMEndpoint, ModelDefinition
from packages.domain.policy import PolicyDefinition, PolicyRule
from packages.domain.protocols import (
    CompiledRunPlan,
    FindingSeverity,
    PhaseStrategy,
    ProtocolDefinition,
    ProtocolPhase,
    RoleRequirement,
)
from packages.domain.roles import (
    AgentBinding,
    AgentSpec,
    ModelCapabilityRequirement,
    RoleDefinition,
    RolePool,
    TeamTemplate,
)
from packages.domain.tasks import AcceptanceCriterion, TaskContract
from packages.domain.tools import ToolProviderSpec
from packages.domain.workspace import Workspace


class Credentials:
    def resolve(self, credential_ref: str) -> SecretValue:
        return SecretValue(f"value-for-{credential_ref}")


def protocol() -> ProtocolDefinition:
    return ProtocolDefinition(
        id="simple_protocol_v0_4_0",
        version=Version("0.4.0"),
        phases=[
            ProtocolPhase(
                id="collect",
                strategy=PhaseStrategy.SINGLE_AGENT,
                required_roles=[RoleRequirement("researcher", 1, 1)],
                required_capabilities=["literature.search"],
                task_contract="research",
                timeout_seconds=10,
            )
        ],
    )


def _role() -> RoleDefinition:
    return RoleDefinition(
        id="researcher",
        role_type="Researcher",
        category=RoleCategory.DISCOVERY,
        activation_default=ActivationPolicy.REQUIRED_BY_PROTOCOL,
        hard_model_capabilities=ModelCapabilityRequirement(all_of=["CHAT"]),
    )


def _agent() -> AgentSpec:
    return AgentSpec(
        id="agent-1",
        role="researcher",
        model_binding=AgentBinding(mode=ModelBindingMode.EXPLICIT_MODEL, value="model-1"),
    )


def _model() -> ModelDefinition:
    return ModelDefinition(
        id="model-1",
        endpoint_id="endpoint-1",
        model_name="fixture-model",
        capabilities={
            ModelCapability.CHAT: CapabilityAssertion(
                status=CapabilityStatus.SUPPORTED,
                confidence=1.0,
                source=CapabilitySource.PROBED,
                probe_version="fixture-v1",
            )
        },
    )


def _endpoint() -> LLMEndpoint:
    return LLMEndpoint(
        id="endpoint-1",
        name="Fixture endpoint",
        protocol="OPENAI_COMPATIBLE",
        base_url="https://relay.example.test",
        credential_ref="fixture-key",
    )


def _contract() -> TaskContract:
    return TaskContract(
        id="research",
        version="1.0.0",
        purpose="Collect fixture evidence",
        required_capabilities=["literature.search"],
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.SCHEMA_VALID)],
    )


def _tool_providers() -> dict[str, ToolProviderSpec]:
    return {
        "fixture-tools": ToolProviderSpec(
            id="fixture-tools",
            kind=ProviderType.NATIVE,
            trust_level=TrustLevel.BUILT_IN,
            capabilities=["literature.search"],
            effect_class=EffectClass.READ_ONLY,
        )
    }


def _workspaces() -> dict[str, Workspace]:
    return {
        "workspace": Workspace(
            id="workspace",
            name="Fixture workspace",
            trust_profile=TrustProfile.SANDBOXED_STANDARD,
        )
    }


def _budget_policy() -> BudgetPolicy:
    return BudgetPolicy(
        id="budget",
        hard_limits={"agent_sessions": 1, "tool_requests": 1, "wall_clock_seconds": 10},
    )


def _policy() -> PolicyDefinition:
    return PolicyDefinition(
        id="project-policy",
        version=Version("0.4.0"),
        default_effect=PolicyDecision.DENY,
        allow=(
            PolicyRule(
                capability="literature.search",
                scope="approved_tool_providers",
            ),
        ),
    )


def catalog() -> CatalogSnapshot:
    return CatalogSnapshot(
        roles={"researcher": _role()},
        agents={"agent-1": _agent()},
        team_templates={
            "team": TeamTemplate(
                id="team",
                display_name="Fixture Team",
                roles={"researcher": RolePool(min_instances=1, max_instances=1)},
            )
        },
        models={"model-1": _model()},
        task_contracts={"research": _contract()},
        endpoints={"endpoint-1": _endpoint()},
        tool_providers=_tool_providers(),
        workspaces=_workspaces(),
        budget_policies={"budget": _budget_policy()},
        policy=_policy(),
    )


def context(catalog_snapshot: CatalogSnapshot | None = None) -> PreflightContext:
    return PreflightContext(
        catalog=catalog_snapshot or catalog(),
        project=ProjectSettings(
            project_id="project-1",
            team_template_id="team",
            default_model_profile_id=None,
            budget_policy_id="budget",
            workspace_backend="workspace",
        ),
        credentials=Credentials(),
        endpoint_health={"endpoint-1": EndpointHealth.HEALTHY},
        policy_evaluator=NativePolicyEvaluator(_policy()),
    )


def compiled() -> tuple[CompiledRunPlan, PreflightContext]:
    catalog_snapshot = catalog()
    result = compile_protocol(protocol(), catalog_snapshot, context(catalog_snapshot).project)
    assert result.plan is not None
    assert not any(finding.severity is FindingSeverity.ERROR for finding in result.findings), (
        result.findings
    )
    return result.plan, context(catalog_snapshot)


__all__ = ["catalog", "compiled", "context", "protocol"]
