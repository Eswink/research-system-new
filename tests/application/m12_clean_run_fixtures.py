"""M12 clean-run 测试 fixtures（M12-R1 WP8）。

与生产 clean_run 标识一致：experiment_run_id 由 experiment_run_id_of(run_id)
确定性派生；fake 执行器模拟真实容器产出（含 image_digest / elapsed 观测）。
"""

from __future__ import annotations

import json
from pathlib import Path

from adapters.fakes import (
    FakeArtifactStore,
    FakeBudgetLedger,
    FakeEvidenceLedger,
    FakeMemoryStore,
    FakeWorkspaceBackend,
)
from packages.application.m12_reference.clean_run_stages import experiment_run_id_of
from packages.application.m12_reference.deps import CleanRunDeps
from packages.application.policy.native import NativePolicyEvaluator
from packages.application.ports import PreflightContext, ProjectSettings
from packages.application.ports.credential_resolver import SecretValue
from packages.domain.budget import BudgetPolicy
from packages.domain.core import ID, Version
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
)
from packages.domain.models import CapabilityAssertion, LLMEndpoint, ModelDefinition
from packages.domain.policy import PolicyDefinition, PolicyRule
from packages.domain.protocols import (
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
from packages.domain.workspace import ExecutionRun, ExecutionStatus, Workspace

RUN_ID = "12121212-2222-4333-8444-555555555555"
PLAN_ID = ID("5a1c6a8e-9b2d-4f3a-8c5e-2b2c3d4e5f6a")
EXPERIMENT_RUN_ID = experiment_run_id_of(RUN_ID)
COMMAND = "python experiment.py"
IMAGE_DIGEST = "sha256:sandbox-image"


class _Credentials:
    def resolve(self, credential_ref: str) -> SecretValue:
        return SecretValue("fixture-secret")


class ResultWritingExecution:
    """执行后写入真实 experiment_result.json 的 fake（模拟容器产出）。

    携带 backend 观测（image_digest / elapsed_seconds），使 audit 与
    budget 与真实执行路径同构。
    """

    def __init__(self, workspace_root: Path) -> None:
        self._root = workspace_root
        self._counter = 0

    def execute(self, spec: object, timeout_seconds: int | None = None) -> ExecutionRun:
        from packages.domain.core import Timestamp

        self._counter += 1
        payload = {
            "experiment_run_id": EXPERIMENT_RUN_ID,
            "status": "SUCCEEDED",
            "artifact_refs": ["experiment_result.json"],
            "metrics": {
                "baseline_accuracy": "0.745",
                "candidate_accuracy": "0.28",
                "n_train": 500,
                "n_test": 200,
            },
            "results": {
                "baseline": {"method": "tfidf", "metrics": {"accuracy": "0.745"}},
                "candidate": {"method": "hash", "metrics": {"accuracy": "0.28"}},
            },
            "seed": 7,
            "image_digest": IMAGE_DIGEST,
        }
        (self._root / "experiment_result.json").write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8"
        )
        now = Timestamp.now()
        return ExecutionRun(
            run_id=f"exec-{self._counter}",
            spec=spec,  # type: ignore[arg-type]  # fixture 的 ExecutionSpec 构造
            status=ExecutionStatus.SUCCEEDED,
            started_at=now,
            completed_at=now,
            exit_code=0,
            compute_usage_summary={
                "exit_code": 0,
                "elapsed_seconds": 12.5,
                "image_digest": IMAGE_DIGEST,
            },
        )

    def close(self) -> None:
        return None


def protocol() -> ProtocolDefinition:
    return ProtocolDefinition(
        id="m12_reference_research_v1_0_0",
        version=Version("0.4.0"),
        phases=[
            ProtocolPhase(
                id="execution",
                strategy=PhaseStrategy.SINGLE_AGENT,
                required_roles=[RoleRequirement("researcher", 1, 1)],
                task_contract="research",
                timeout_seconds=60,
            )
        ],
    )


def catalog() -> object:
    from packages.application.ports import CatalogSnapshot

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
        tool_providers={"fixture-tools": _tool()},
        workspaces={"workspace": Workspace(id="workspace", name="workspace")},
        budget_policies={
            "budget": BudgetPolicy(
                id="budget",
                hard_limits={
                    "agent_sessions": 1,
                    "tool_requests": 1,
                    "wall_clock_seconds": 60,
                },
            )
        },
        policy=_policy(),
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
        purpose="Run fixture experiment",
        required_capabilities=["literature.search"],
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.SCHEMA_VALID)],
    )


def _tool() -> ToolProviderSpec:
    return ToolProviderSpec(
        id="fixture-tools",
        kind=ProviderType.NATIVE,
        trust_level=TrustLevel.BUILT_IN,
        capabilities=["literature.search"],
        effect_class=EffectClass.READ_ONLY,
    )


def _policy() -> PolicyDefinition:
    return PolicyDefinition(
        id="project-policy",
        version=Version("0.4.0"),
        default_effect=PolicyDecision.DENY,
        allow=(PolicyRule(capability="literature.search", scope="approved_tool_providers"),),
    )


def make_deps(tmp_path: Path) -> CleanRunDeps:
    from packages.application.ports import CatalogSnapshot

    cat = catalog()
    assert isinstance(cat, CatalogSnapshot)
    project = ProjectSettings(
        project_id="project-1",
        team_template_id="team",
        default_model_profile_id=None,
        budget_policy_id="budget",
        workspace_backend="workspace",
    )
    context = PreflightContext(
        catalog=cat,
        project=project,
        credentials=_Credentials(),
        endpoint_health={"endpoint-1": EndpointHealth.HEALTHY},
        policy_evaluator=NativePolicyEvaluator(cat.policy),  # type: ignore[arg-type]
    )
    workspace_root = tmp_path / "workspace-root"
    workspace_root.mkdir(parents=True, exist_ok=True)
    workspaces = FakeWorkspaceBackend()
    workspaces.create_workspace(Workspace(id="workspace", name="workspace"))
    return CleanRunDeps(
        protocol=protocol(),
        catalog=cat,
        project=project,
        context=context,
        execution=ResultWritingExecution(workspace_root),
        workspaces=workspaces,
        workspace=Workspace(id="workspace", name="workspace"),
        artifacts=FakeArtifactStore(),
        ledger=FakeEvidenceLedger(),
        memory=FakeMemoryStore(allowed_sources=(f"{EXPERIMENT_RUN_ID}:experiment_result.json",)),
        budget=FakeBudgetLedger(),
        run_id=RUN_ID,
        workspace_root=workspace_root,
    )


__all__ = [
    "COMMAND",
    "EXPERIMENT_RUN_ID",
    "IMAGE_DIGEST",
    "PLAN_ID",
    "RUN_ID",
    "ResultWritingExecution",
    "catalog",
    "make_deps",
    "protocol",
]
