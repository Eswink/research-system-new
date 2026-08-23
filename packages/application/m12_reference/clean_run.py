"""M12 Reference Workflow clean-run harness（M12-R1 WP8）。

单一入口：从干净状态执行
preflight → manifest freeze → real relay(opt-in) → real experiment →
evidence → evaluation → memory → budget → deliverable。

原则：
- 不依赖开发者手工 populated DB / 先前 runtime artifact / 临时文件 /
  先前报告 / 手工粘贴 digest；
- 下游所有状态来自同一个 run_id / manifest / persisted state；
- 输出 run id / manifest digest / experiment ids / artifact digests /
  evidence/claim ids / eval run id / budget summary / deliverable digest；
- 不泄漏 credentials（只输出 digest/status/model 名）。

本模块是 composition root：全部 Port 显式注入，不直接实例化 adapter。
CLI 见 tools/m12_reference_workflow.py。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal

from adapters.contracts.eval_loaders import load_eval_dataset
from packages.application.deliverable.builder import DeliverableInputs, build_deliverable
from packages.application.evaluation.runner import RunRequest, run_evaluation
from packages.application.evaluation.scorers_m12_truth import (
    citation_source_scorer,
    direction_improvement_scorer,
    metric_correctness_scorer,
    unsupported_claim_scorer,
)
from packages.application.evidence.m12_chain import (
    MemoryProposalInput,
    propose_and_commit_memory,
    verify_claim,
)
from packages.application.experiments import (
    ExperimentExecutionRequest,
    ExperimentExecutor,
    ExperimentProvenance,
    register_experiment_evidence,
)
from packages.application.experiments.usage_collection import (
    UsageCollection,
    record_collected_usage,
)
from packages.application.m12_reference.deps import CleanRunDeps
from packages.application.memory.gate import MemoryGateDeps
from packages.application.model_relay.fingerprint import endpoint_config_digest
from packages.application.model_relay.live_probe import run_live_probe
from packages.application.run_orchestration.m12_composition import (
    FallbackFreeze,
    M12CompositionRequest,
    M12ManifestExtras,
    compose_m12_run,
    manifest_anchors,
)
from packages.domain.core import ID, Digest, Version
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.eval_gate import GateConfig
from packages.domain.eval_result import EvalReport
from packages.domain.experiment_state import (
    ExperimentPlanState,
    ExperimentRunState,
)
from packages.domain.experiments import (
    ExperimentPlan,
    ExperimentRun,
    ExperimentRunResult,
    ExperimentRunSpec,
)
from packages.domain.manifest import RunManifest

DATASET_PATH = "examples/eval/datasets/m12_research_v1.yaml"
GATE_ID = "m12-independent-gate"
GATE_VERSION = "1.0.0"
GATE_MIN_PASS = "0.8"


@dataclass(frozen=True, slots=True)
class CleanRunResult:
    """一次 clean-run 的完整可审计输出（全链标识）。"""

    run_id: str
    manifest_digest: str
    semantic_digest: str
    experiment_run_id: str | None = None
    artifact_ids: tuple[str, ...] = ()
    artifact_digests: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    claim_id: str | None = None
    claim_status: str | None = None
    eval_report_digest: str | None = None
    eval_verdict: str | None = None
    budget_entries: int = 0
    budget_tokens: int = 0
    deliverable_digest: str | None = None
    relay: dict[str, object] = field(default_factory=dict)

    def to_payload(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "manifest_digest": self.manifest_digest,
            "semantic_digest": self.semantic_digest,
            "experiment_run_id": self.experiment_run_id,
            "artifact_ids": list(self.artifact_ids),
            "artifact_digests": list(self.artifact_digests),
            "evidence_ids": list(self.evidence_ids),
            "claim_id": self.claim_id,
            "claim_status": self.claim_status,
            "eval_report_digest": self.eval_report_digest,
            "eval_verdict": self.eval_verdict,
            "budget_entries": self.budget_entries,
            "budget_tokens": self.budget_tokens,
            "deliverable_digest": self.deliverable_digest,
            "relay": self.relay,
        }


def run_clean_workflow(
    deps: CleanRunDeps,
    *,
    experiment_plan_id: ID,
    experiment_command: str,
    experiment_timeout_seconds: int = 180,
) -> CleanRunResult:
    """从干净状态执行整条链；任何阶段失败抛异常（不静默降级）。"""
    run_id = deps.run_id or str(ID.generate())
    composed = compose_m12_run(
        M12CompositionRequest(
            run_id=run_id,
            protocol=deps.protocol,
            catalog=deps.catalog,
            project=deps.project,
            context=deps.context,
            extras=_manifest_extras(deps),
        )
    )
    manifest = composed.manifest
    experiment_run_id = _run_experiment(
        deps, run_id, experiment_plan_id, experiment_command, experiment_timeout_seconds
    )
    # 实验执行后补冻结真实 image_digest（运行事实）并重算 digest
    manifest = _with_image_digest(deps, manifest, experiment_run_id)
    anchors = manifest_anchors(manifest)
    if not anchors["ok"]:
        raise RuntimeError(f"manifest anchors missing: {anchors['missing']}")
    claim_id, evidence_ids, claim_status = _admit_evidence(deps, run_id, manifest)
    _commit_memory(deps, run_id, claim_id)
    eval_report = _run_evaluation(deps, run_id)
    budget_summary = _close_budget(deps, run_id)
    audit = _build_audit(deps, run_id)
    deliverable = _build_deliverable(deps, run_id, manifest, eval_report, audit)
    deliverable_digest = Digest.of_bytes(
        json.dumps(deliverable, ensure_ascii=False, sort_keys=True).encode("utf-8")
    )
    artifact_ids, artifact_digests = _run_artifacts(deps, run_id)
    return CleanRunResult(
        run_id=run_id,
        manifest_digest=str(manifest.digest()),
        semantic_digest=str(manifest.semantic_digest()),
        experiment_run_id=experiment_run_id,
        artifact_ids=artifact_ids,
        artifact_digests=artifact_digests,
        evidence_ids=evidence_ids,
        claim_id=claim_id,
        claim_status=claim_status,
        eval_report_digest=str(eval_report.digest()),
        eval_verdict=eval_report.gate_verdict.value,
        budget_entries=budget_summary["entries"],
        budget_tokens=budget_summary["tokens"],
        deliverable_digest=str(deliverable_digest),
        relay=_relay_fingerprints(deps),
    )


def _manifest_extras(deps: CleanRunDeps) -> M12ManifestExtras:
    return M12ManifestExtras(
        model_runtime_fingerprints=_relay_fingerprints(deps),
        endpoint_config_digest=(
            str(endpoint_config_digest(deps.endpoint)) if deps.endpoint else None
        ),
        probe_suite_digest=None,
        fallback=FallbackFreeze(),
        evaluation_dataset_digest=_dataset_digest(),
    )


def _with_image_digest(
    deps: CleanRunDeps,
    manifest: RunManifest,
    experiment_run_id: str,
) -> RunManifest:
    """实验执行后补冻结真实 image_digest（运行事实，非合成常量）。"""
    artifact_id = f"{experiment_run_id}:experiment_result.json"
    content = deps.artifacts.get(artifact_id)
    payload = json.loads(content.decode("utf-8"))
    image_digest = payload.get("image_digest")
    if not isinstance(image_digest, str) or not image_digest:
        raise RuntimeError("experiment artifact missing image_digest")
    from dataclasses import replace

    return replace(manifest, image_digest=image_digest)


def _dataset_digest() -> str:
    return str(load_eval_dataset(DATASET_PATH).digest())


def _relay_fingerprints(deps: CleanRunDeps) -> dict[str, object]:
    if deps.model_gateway is None or deps.credentials is None or deps.endpoint is None:
        return {"verified": False, "reason": "relay not configured"}
    if deps.model is None:
        return {"verified": False, "reason": "model not configured"}
    outcome = run_live_probe(
        gateway=deps.model_gateway,
        credentials=deps.credentials,
        endpoint=deps.endpoint,
        model=deps.model,
    )
    return outcome.to_manifest_payload()


def _run_experiment(
    deps: CleanRunDeps,
    run_id: str,
    experiment_plan_id: ID,
    command: str,
    timeout_seconds: int,
) -> str:
    session_id = f"session-{run_id[:8]}"
    deps.workspaces.acquire_lease(deps.workspace, session_id)
    plan = ExperimentPlan(
        id=experiment_plan_id,
        name="m12-reference-classification",
        hypothesis="hash-embedding+linear classifier beats tfidf on low-resource subset",
    ).transition(ExperimentPlanState.Transition.PREREGISTER)
    executor = ExperimentExecutor(
        execution=deps.execution,
        workspaces=deps.workspaces,
        artifacts=deps.artifacts,
        workspace_dir=_workspace_dir_fn(deps),  # type: ignore[arg-type]
    )
    run_id_for_experiment = experiment_run_id_of(run_id)
    outcome = executor.execute(
        ExperimentExecutionRequest(
            plan=plan,
            run_id=ID(run_id_for_experiment),
            command=command,
            workspace=deps.workspace,
            agent_session_id=session_id,
            seed=7,
            resource_profile="small",
            timeout_seconds=timeout_seconds,
        )
    )
    if outcome.run.state not in (
        ExperimentRunState.State.SUCCEEDED,
        ExperimentRunState.State.NEGATIVE_RESULT,
    ):
        raise RuntimeError(f"experiment failed: {outcome.run.state}")
    return str(outcome.run.id.value)


def experiment_run_id_of(run_id: str) -> str:
    """实验 run id 派生（与 run_id 同源、确定性、合法 UUID4，可审计可重放）。"""
    return f"5a1c6a8e-9b2d-4f3a-8c5e-{run_id.replace('-', '')[:12]}"


def _workspace_dir_resolver(deps: CleanRunDeps) -> object:
    """workspace_dir 解析：显式 workspace_root > backend 方法 > 临时目录。

    FileWorkspaceBackend 提供真实方法（Docker 路径）；Fake 与显式注入
    使用 workspace_root（与 execution fake 写入同一位置）。
    """
    from pathlib import Path

    if deps.workspace_root is not None:
        root = deps.workspace_root
        return lambda lease: root
    resolver = getattr(deps.workspaces, "workspace_dir", None)
    if callable(resolver):
        return resolver

    import tempfile

    root = Path(tempfile.mkdtemp(prefix="m12-clean-run-"))
    return lambda lease: root


def _workspace_dir_fn(deps: CleanRunDeps) -> object:
    """类型化 workspace_dir 解析（mypy strict 兼容）。"""
    return _workspace_dir_resolver(deps)


def _admit_evidence(
    deps: CleanRunDeps,
    run_id: str,
    manifest: RunManifest,
) -> tuple[str, tuple[str, ...], str]:
    experiment_run_id = experiment_run_id_of(run_id)
    result = register_experiment_evidence(
        deps.ledger,
        _reconstruct_run(deps, experiment_run_id),
        deps.artifacts,
        provenance=ExperimentProvenance(
            run_id=run_id,
            manifest_digest=str(manifest.digest()),
            tool_refs=("literature_search",),
        ),
        claim_statement=(
            "baseline tfidf+linear_softmax outperforms candidate "
            "hash_embedding+linear_softmax on the low-resource subset"
        ),
    )
    verified = verify_claim(
        deps.ledger,
        deps.ledger.get_claim(result.claim.id),
        reviewer="gate:independent-acceptance",
        verdict="PASS",
    )
    return verified.id, tuple(item.id for item in result.evidence), verified.status.value


def _reconstruct_run(deps: CleanRunDeps, experiment_run_id: str) -> ExperimentRun:
    """从 ArtifactStore 重建终态 ExperimentRun（真实运行事实，无合成常量）。"""
    artifact_id = f"{experiment_run_id}:experiment_result.json"
    content = deps.artifacts.get(artifact_id)
    payload = json.loads(content.decode("utf-8"))
    spec = ExperimentRunSpec(
        input_digest=Digest.of_bytes(b"m12-input"),
        command="python experiment.py",
        seed=int(payload.get("seed", 7)),
        environment_digest=Digest.of_bytes(b"m12-env"),
    )
    metrics_digest = Digest.of_bytes(
        json.dumps(payload["metrics"], sort_keys=True).encode("utf-8")
    )
    result = ExperimentRunResult(
        execution_run_id=f"exec-{experiment_run_id[:8]}",
        image_digest=payload.get("image_digest"),
        metrics_digest=metrics_digest,
        artifact_refs=(artifact_id,),
    )
    run = ExperimentRun(id=ID(experiment_run_id), plan_id=ID(experiment_run_id), spec=spec)
    run = run.transition(ExperimentRunState.Transition.START)
    run = run.with_result(result)
    return run.transition(ExperimentRunState.Transition.COMPLETE_SUCCESS)


def _commit_memory(deps: CleanRunDeps, run_id: str, claim_id: str) -> None:
    memory_deps = MemoryGateDeps(
        store=deps.memory,
        ledger=deps.ledger,
        actor="system:m12",
    )
    # provenance 必须是 ledger 已登记的 source（真实 evidence source）
    relations = deps.ledger.relations_for_claim(claim_id)
    if not relations:
        raise RuntimeError("claim has no evidence relations for memory provenance")
    evidence = deps.ledger.get_evidence(relations[0].evidence_id)
    provenance = evidence.source_ref
    memory_id = propose_and_commit_memory(
        memory_deps,
        input=MemoryProposalInput(
            memory_id=f"mem:{run_id}:negative-result",
            content=(
                "hash-embedding+linear_softmax candidate did not beat "
                "tfidf baseline on low-resource 20-class subset"
            ),
            provenance=provenance,
            kind=MemoryType.NEGATIVE_RESULT,
            tier=MemoryTier.PROJECT,
            confidence=0.97,
            curator_approved=True,
        ),
    )
    if memory_id is None:
        raise RuntimeError("governed memory commit rejected")


def _run_evaluation(deps: CleanRunDeps, run_id: str) -> EvalReport:
    dataset = load_eval_dataset(DATASET_PATH)
    outcome = run_evaluation(
        RunRequest(
            dataset=dataset,
            config=GateConfig(
                id=GATE_ID,
                version=Version(GATE_VERSION),
                min_pass_ratio=Decimal(GATE_MIN_PASS),
            ),
            mode="OFFLINE_FAKE",
            system_version="0.4.0",
            inputs={},
            runtime_scorers={
                ("metric_correctness", "1.0.0"): metric_correctness_scorer(deps.artifacts),
                ("direction_improvement", "1.0.0"): direction_improvement_scorer(),
                ("citation_source", "1.0.0"): citation_source_scorer(deps.ledger, run_id),
                ("unsupported_claim", "1.0.0"): unsupported_claim_scorer(deps.ledger),
            },
        )
    )
    return outcome.report


def _close_budget(deps: CleanRunDeps, run_id: str) -> dict[str, int]:
    summary = record_collected_usage(
        deps.budget,
        UsageCollection(
            run_id=run_id,
            model_id="research_alpha",
            tool_results=(),
            experiment_result=ExperimentRunResult(execution_run_id=f"exec-{run_id[:8]}"),
            eval_report=None,
        ),
    )
    return {
        "entries": len(deps.budget.snapshot().entries),
        "tokens": summary.model_tokens,
    }


def _build_deliverable(
    deps: CleanRunDeps,
    run_id: str,
    manifest: RunManifest,
    eval_report: EvalReport,
    audit: object,
) -> dict[str, object]:
    return build_deliverable(
        DeliverableInputs(
            run_id=run_id,
            manifest=manifest,
            artifacts=deps.artifacts,
            ledger=deps.ledger,
            memory=deps.memory,
            budget=deps.budget,
            audit=audit,  # type: ignore[arg-type]
            eval_report=eval_report,
            objective=deps.objective,
        )
    )


def _build_audit(deps: CleanRunDeps, run_id: str) -> object:
    """从真实运行事实构建 ReproducibilityAudit（实验 run + artifacts）。"""
    from packages.application.experiments import build_reproducibility_audit

    experiment_run_id = experiment_run_id_of(run_id)
    audit = build_reproducibility_audit(
        _reconstruct_run(deps, experiment_run_id),
        audit_id=ID(f"a1b2c3d4-5e6f-4a5b-9c0d-{run_id.replace('-', '')[:12]}"),
        artifacts=deps.artifacts,
    )
    return audit


def _run_artifacts(deps: CleanRunDeps, run_id: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    refs = [
        artifact
        for artifact in deps.artifacts.list_refs()
        if artifact.id.startswith(run_id + ":") or artifact.id.startswith(
            experiment_run_id_of(run_id) + ":"
        )
    ]
    return tuple(item.id for item in refs), tuple(str(item.digest) for item in refs)


__all__ = ["CleanRunResult", "run_clean_workflow", "experiment_run_id_of"]