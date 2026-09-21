"""M7 E2E catalog fixture：sort-analysis-v1 场景的领域资源目录。"""

from __future__ import annotations

from adapters.fakes.credential_resolver import FakeCredentialResolver
from adapters.fakes.policy_evaluator import FakePolicyEvaluator
from packages.application.ports.resource_catalog import (
    CatalogSnapshot,
    PreflightContext,
    ProjectSettings,
)
from packages.domain.budget import BudgetPolicy
from packages.domain.core import Version
from packages.domain.enums import (
    AcceptanceCriterionType,
    ActivationPolicy,
    BackendKind,
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
    WorkspacePolicy,
)
from packages.domain.models import CapabilityAssertion, LLMEndpoint, ModelDefinition
from packages.domain.policy import PolicyDefinition, PolicyRule
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


def _role_engineer() -> RoleDefinition:
    return RoleDefinition(
        id="experiment_engineer",
        role_type="ExperimentEngineer",
        category=RoleCategory.EXPERIMENT,
        activation_default=ActivationPolicy.REQUIRED_BY_PROTOCOL,
        requested_capabilities=[
            "workspace.read",
            "workspace.write.code",
            "code.execute",
            "artifact.write",
        ],
        hard_model_capabilities=ModelCapabilityRequirement(
            all_of=[ModelCapability.CHAT.value, ModelCapability.TOOL_CALLING_NATIVE.value]
        ),
        workspace_policy=WorkspacePolicy.ISOLATED_WRITABLE,
    )


def _role_reviewer() -> RoleDefinition:
    return RoleDefinition(
        id="scientific_reviewer",
        role_type="ScientificReviewer",
        category=RoleCategory.EVALUATION,
        activation_default=ActivationPolicy.REQUIRED_BY_PROTOCOL,
        requested_capabilities=["workspace.read", "evidence.read"],
        hard_model_capabilities=ModelCapabilityRequirement(all_of=[ModelCapability.CHAT.value]),
        workspace_policy=WorkspacePolicy.READ_ONLY,
    )


def _agent_engineer() -> AgentSpec:
    return AgentSpec(
        id="engineer-1",
        role="experiment_engineer",
        model_binding=AgentBinding(ModelBindingMode.EXPLICIT_MODEL, "model-engineer"),
        runtime_kind=BackendKind.OPENHANDS_NATIVE,
    )


def _agent_reviewer() -> AgentSpec:
    return AgentSpec(
        id="reviewer-1",
        role="scientific_reviewer",
        model_binding=AgentBinding(ModelBindingMode.EXPLICIT_MODEL, "model-reviewer"),
        workspace_policy=WorkspacePolicy.READ_ONLY,
        runtime_kind=BackendKind.OPENHANDS_NATIVE,
    )


def _model(model_id: str, capabilities: tuple[ModelCapability, ...]) -> ModelDefinition:
    return ModelDefinition(
        id=model_id,
        endpoint_id="relay-main",
        model_name=model_id,
        capabilities={
            capability: CapabilityAssertion(
                status=CapabilityStatus.SUPPORTED,
                confidence=1.0,
                source=CapabilitySource.PROBED,
                probe_version="m7-fixture-v1",
            )
            for capability in capabilities
        },
    )


def _endpoint() -> LLMEndpoint:
    return LLMEndpoint(
        id="relay-main",
        name="M7 relay",
        protocol="OPENAI_COMPATIBLE",
        base_url="https://relay.example.test/v1",
        credential_ref="llm_m7_key",
    )


def _execution_contract() -> TaskContract:
    return TaskContract(
        id="sort_analysis_execution",
        version="1.0.0",
        purpose="Analyze the input algorithm repository and produce a report artifact.",
        required_capabilities=["workspace.read", "workspace.write.code", "code.execute"],
        acceptance_criteria=[
            AcceptanceCriterion(
                type=AcceptanceCriterionType.ARTIFACT_EXISTS,
                artifact="analysis_report",
            )
        ],
        timeout_seconds=120,
        retry_policy=None,
    )


def _review_contract() -> TaskContract:
    """独立复核合约。

    `ARTIFACT_EXISTS`（GOAL-010 EC-02 之后补）：F-12 场景（review 只回一个字符串、
    产不出制品）此前**仅仅**因为 `EVIDENCE_COVERAGE` 的旧口径（`len(evidence)`）才判拒。
    覆盖判据收紧成「非模型自述的来源」后，本合约声明的输入使覆盖**如实**通过——
    于是「review 什么都不产出也算过」这个洞暴露出来。它从来不是覆盖判据该管的事，
    而是本合约**欠声明**：协议写了 `outputs: [review_decision]`，合约却没要求它存在。
    补上这条是**收紧**不是放宽——空复核仍然判拒，且理由指向它自己没交货。
    """
    return TaskContract(
        id="sort_analysis_review",
        version="1.0.0",
        purpose="Independently review the analysis report against the artifact.",
        required_capabilities=["workspace.read", "evidence.read"],
        acceptance_criteria=[
            AcceptanceCriterion(
                type=AcceptanceCriterionType.ARTIFACT_EXISTS,
                artifact="review_decision",
            ),
            AcceptanceCriterion(
                type=AcceptanceCriterionType.EVIDENCE_COVERAGE,
                minimum_sources=1,
            ),
        ],
        timeout_seconds=60,
        retry_policy=None,
    )


def _providers() -> dict[str, ToolProviderSpec]:
    return {
        "bash_read_only": ToolProviderSpec(
            id="bash_read_only",
            kind=ProviderType.NATIVE,
            trust_level=TrustLevel.BUILT_IN,
            capabilities=["workspace.read", "code.execute"],
            effect_class=EffectClass.READ_ONLY,
        ),
        "artifact_writer": ToolProviderSpec(
            id="artifact_writer",
            kind=ProviderType.NATIVE,
            trust_level=TrustLevel.BUILT_IN,
            capabilities=["workspace.write.code", "artifact.write"],
            effect_class=EffectClass.WRITE,
        ),
        "evidence_provider": ToolProviderSpec(
            id="evidence_provider",
            kind=ProviderType.NATIVE,
            trust_level=TrustLevel.BUILT_IN,
            capabilities=["evidence.read"],
            effect_class=EffectClass.READ_ONLY,
        ),
    }


def _budget_policy() -> BudgetPolicy:
    return BudgetPolicy(
        id="m7_budget",
        hard_limits={"agent_sessions": 2, "tool_requests": 10, "wall_clock_seconds": 300},
    )


def _policy() -> PolicyDefinition:
    return PolicyDefinition(
        id="project-policy",
        version=Version("0.4.0"),
        default_effect=PolicyDecision.DENY,
        allow=(
            PolicyRule(capability="workspace.read"),
            PolicyRule(capability="workspace.write.code"),
            PolicyRule(capability="code.execute"),
            PolicyRule(capability="artifact.write"),
            PolicyRule(capability="evidence.read"),
        ),
    )


def m7_catalog() -> CatalogSnapshot:
    return CatalogSnapshot(
        roles={
            "experiment_engineer": _role_engineer(),
            "scientific_reviewer": _role_reviewer(),
        },
        agents={"engineer-1": _agent_engineer(), "reviewer-1": _agent_reviewer()},
        team_templates={
            "m7_team": TeamTemplate(
                id="m7_team",
                display_name="M7 Reference Team",
                roles={
                    "experiment_engineer": RolePool(min_instances=1, max_instances=1),
                    "scientific_reviewer": RolePool(min_instances=1, max_instances=1),
                },
            )
        },
        models={
            "model-engineer": _model(
                "model-engineer", (ModelCapability.CHAT, ModelCapability.TOOL_CALLING_NATIVE)
            ),
            "model-reviewer": _model("model-reviewer", (ModelCapability.CHAT,)),
        },
        task_contracts={
            "sort_analysis_execution": _execution_contract(),
            "sort_analysis_review": _review_contract(),
        },
        endpoints={"relay-main": _endpoint()},
        tool_providers=_providers(),
        workspaces={
            "sandbox": Workspace(
                id="sandbox",
                name="M7 sandbox",
                trust_profile=TrustProfile.SANDBOXED_STANDARD,
            )
        },
        budget_policies={"m7_budget": _budget_policy()},
        policy=_policy(),
    )


def m7_project() -> ProjectSettings:
    return ProjectSettings(
        project_id="m7-project",
        team_template_id="m7_team",
        default_model_profile_id=None,
        budget_policy_id="m7_budget",
        workspace_backend="sandbox",
    )


def m7_preflight_context(
    catalog: CatalogSnapshot,
    project: ProjectSettings,
    evaluator: FakePolicyEvaluator | None = None,
    budget_ledger: object | None = None,
) -> PreflightContext:
    return PreflightContext(
        catalog=catalog,
        project=project,
        credentials=FakeCredentialResolver({"llm_m7_key": "sk-m7"}),
        endpoint_health={"relay-main": EndpointHealth.HEALTHY},
        budget_ledger=budget_ledger,  # type: ignore[arg-type]
        policy_evaluator=evaluator or FakePolicyEvaluator(),
    )
