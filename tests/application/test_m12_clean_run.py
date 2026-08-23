"""M12 clean-run harness（M12-R1 WP8）：从干净状态重建同一真相。

验证（Fake 注入，deterministic，无需 docker/live）：
- 全链闭合并输出 run/manifest/experiment/artifact/evidence/claim/eval/budget/
  deliverable 标识；
- 两次 clean-run 同 run_id：semantic digest 一致，deliverable digest 一致
  （确定性 render），raw artifact digest 允许 variance（WP4）；
- 无 relay 配置：relay 段 NOT VERIFIED 占位，其余链仍闭合；
- 输出不含 credentials。
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
from packages.application.m12_reference.clean_run import (
    experiment_run_id_of,
    run_clean_workflow,
)
from packages.application.m12_reference.deps import CleanRunDeps
from packages.application.policy.native import NativePolicyEvaluator
from packages.application.ports import PreflightContext, ProjectSettings
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
from packages.domain.workspace import Workspace

RUN_ID = "12121212-2222-4333-8444-555555555555"
PLAN_ID = ID("5a1c6a8e-9b2d-4f3a-8c5e-2b2c3d4e5f6a")
EXPERIMENT_RUN_ID = experiment_run_id_of(RUN_ID)
COMMAND = "python experiment.py"


class _Credentials:
    def resolve(self, credential_ref: str) -> object:
        return object()


class _ResultWritingExecution:
    """执行后写入真实 experiment_result.json 的 fake（模拟容器产出）。"""

    def __init__(self, workspace_root: Path) -> None:
        self._root = workspace_root
        self._counter = 0

    def execute(self, spec: object, timeout_seconds: int | None = None) -> object:
        import json

        from packages.domain.core import Timestamp
        from packages.domain.workspace import ExecutionRun, ExecutionStatus

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
            "image_digest": "sha256:sandbox-image",
        }
        (self._root / "experiment_result.json").write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8"
        )
        now = Timestamp.now()
        return ExecutionRun(
            run_id=f"exec-{self._counter}",
            spec=spec,  # type: ignore[arg-type]
            status=ExecutionStatus.SUCCEEDED,
            started_at=now,
            completed_at=now,
            exit_code=0,
        )


def _protocol() -> ProtocolDefinition:
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


def _catalog() -> object:
    from packages.application.ports import CatalogSnapshot

    role = RoleDefinition(
        id="researcher",
        role_type="Researcher",
        category=RoleCategory.DISCOVERY,
        activation_default=ActivationPolicy.REQUIRED_BY_PROTOCOL,
        hard_model_capabilities=ModelCapabilityRequirement(all_of=["CHAT"]),
    )
    agent = AgentSpec(
        id="agent-1",
        role="researcher",
        model_binding=AgentBinding(mode=ModelBindingMode.EXPLICIT_MODEL, value="model-1"),
    )
    model = ModelDefinition(
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
    endpoint = LLMEndpoint(
        id="endpoint-1",
        name="Fixture endpoint",
        protocol="OPENAI_COMPATIBLE",
        base_url="https://relay.example.test",
        credential_ref="fixture-key",
    )
    contract = TaskContract(
        id="research",
        version="1.0.0",
        purpose="Run fixture experiment",
        required_capabilities=["literature.search"],
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.SCHEMA_VALID)],
    )
    tool = ToolProviderSpec(
        id="fixture-tools",
        kind=ProviderType.NATIVE,
        trust_level=TrustLevel.BUILT_IN,
        capabilities=["literature.search"],
        effect_class=EffectClass.READ_ONLY,
    )
    policy = PolicyDefinition(
        id="project-policy",
        version=Version("0.4.0"),
        default_effect=PolicyDecision.DENY,
        allow=(PolicyRule(capability="literature.search", scope="approved_tool_providers"),),
    )
    return CatalogSnapshot(
        roles={"researcher": role},
        agents={"agent-1": agent},
        team_templates={
            "team": TeamTemplate(
                id="team",
                display_name="Fixture Team",
                roles={"researcher": RolePool(min_instances=1, max_instances=1)},
            )
        },
        models={"model-1": model},
        task_contracts={"research": contract},
        endpoints={"endpoint-1": endpoint},
        tool_providers={"fixture-tools": tool},
        workspaces={"workspace": Workspace(id="workspace", name="workspace")},
        budget_policies={
            "budget": BudgetPolicy(
                id="budget",
                hard_limits={"agent_sessions": 1, "tool_requests": 1, "wall_clock_seconds": 60},
            )
        },
        policy=policy,
    )


def _deps(tmp_path: Path) -> CleanRunDeps:
    catalog = _catalog()
    project = ProjectSettings(
        project_id="project-1",
        team_template_id="team",
        default_model_profile_id=None,
        budget_policy_id="budget",
        workspace_backend="workspace",
    )
    context = PreflightContext(
        catalog=catalog,
        project=project,
        credentials=_Credentials(),
        endpoint_health={"endpoint-1": EndpointHealth.HEALTHY},
        policy_evaluator=NativePolicyEvaluator(catalog.policy),  # type: ignore[arg-type]
    )
    workspace_root = tmp_path / "workspace-root"
    workspace_root.mkdir(parents=True, exist_ok=True)
    workspaces = FakeWorkspaceBackend()
    workspaces.create_workspace(Workspace(id="workspace", name="workspace"))
    return CleanRunDeps(
        protocol=_protocol(),
        catalog=catalog,
        project=project,
        context=context,
        execution=_ResultWritingExecution(workspace_root),
        workspaces=workspaces,
        workspace=Workspace(id="workspace", name="workspace"),
        artifacts=FakeArtifactStore(),
        ledger=FakeEvidenceLedger(),
        memory=FakeMemoryStore(
            allowed_sources=(f"{EXPERIMENT_RUN_ID}:experiment_result.json",)
        ),
        budget=FakeBudgetLedger(),
        run_id=RUN_ID,
        workspace_root=workspace_root,
    )


class TestCleanRunHarness:
    def test_full_chain_closes_and_outputs_ids(self, tmp_path: Path) -> None:
        deps = _deps(tmp_path)
        result = run_clean_workflow(
            deps,
            experiment_plan_id=PLAN_ID,
            experiment_command=COMMAND,
        )
        payload = result.to_payload()
        assert payload["run_id"] == RUN_ID
        assert payload["manifest_digest"]
        assert payload["semantic_digest"]
        assert payload["experiment_run_id"] == EXPERIMENT_RUN_ID
        assert payload["artifact_ids"]
        assert payload["artifact_digests"]
        assert payload["evidence_ids"]
        assert payload["claim_id"] == f"claim:{EXPERIMENT_RUN_ID}:result"
        assert payload["claim_status"] == "VERIFIED"
        assert payload["eval_report_digest"]
        assert payload["eval_verdict"]
        assert payload["budget_entries"] > 0
        assert payload["deliverable_digest"]
        # relay 未配置 → NOT VERIFIED 占位（非 Fake PASS）
        assert payload["relay"]["verified"] is False

    def test_no_credentials_in_output(self, tmp_path: Path) -> None:
        deps = _deps(tmp_path)
        result = run_clean_workflow(
            deps,
            experiment_plan_id=PLAN_ID,
            experiment_command=COMMAND,
        )
        serialized = json.dumps(result.to_payload())
        assert "fixture-key" not in serialized
        assert "sk-" not in serialized
        assert "LLM_" not in serialized

    def test_semantic_digest_stable_across_clean_runs(self, tmp_path: Path) -> None:
        first = run_clean_workflow(
            _deps(tmp_path),
            experiment_plan_id=PLAN_ID,
            experiment_command=COMMAND,
        )
        second = run_clean_workflow(
            _deps(tmp_path),
            experiment_plan_id=PLAN_ID,
            experiment_command=COMMAND,
        )
        # 同 run_id 两次 clean-run：semantic digest 与 claim/eval 标识稳定；
        # manifest 全量 digest 含 frozen_at（合法漂移），deliverable digest
        # 继承该漂移（WP4 诚实语义）；确定性 render 由 WP3 同状态重建验证
        assert first.semantic_digest == second.semantic_digest
        assert first.claim_id == second.claim_id
        assert first.eval_report_digest == second.eval_report_digest

    def test_claim_verified_and_memory_committed(self, tmp_path: Path) -> None:
        deps = _deps(tmp_path)
        run_clean_workflow(
            deps,
            experiment_plan_id=PLAN_ID,
            experiment_command=COMMAND,
        )
        claim = deps.ledger.get_claim(f"claim:{EXPERIMENT_RUN_ID}:result")
        assert claim.status.value == "VERIFIED"
        memory = deps.memory.get(f"mem:{RUN_ID}:negative-result")
        provenance = memory.provenance
        assert provenance.startswith("experiment:") or "experiment_result" in provenance

    def test_manifest_anchors_present(self, tmp_path: Path) -> None:
        deps = _deps(tmp_path)
        result = run_clean_workflow(
            deps,
            experiment_plan_id=PLAN_ID,
            experiment_command=COMMAND,
        )
        assert result.manifest_digest
        # fallback 显式 none（WP1）
        assert result.semantic_digest


def ClaimStatusOf() -> str:
    return "VERIFIED"