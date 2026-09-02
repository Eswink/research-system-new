"""M12 Reference Workflow clean-run harness（M12-R1 WP8）。

单一入口：从干净状态执行 preflight → manifest freeze → real relay
(opt-in) → real experiment → evidence → evaluation → memory → budget →
deliverable。

原则：不依赖手工 populated DB / 先前产物 / 手工粘贴 digest；下游状态
全部来自同一 run_id / manifest / persisted state；输出全链标识；
不泄漏 credentials；评测 verdict 非 PASS 即失败（fail-closed）；复现
审计绑定真实运行事实。本模块是 composition root：全部 Port 显式注入。
CLI 见 tools/m12_reference_workflow.py。
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from pathlib import Path

from packages.application.experiments import (
    ExperimentExecutionRequest,
    ExperimentExecutor,
)
from packages.application.m12_reference.clean_run_eval import (
    EvalStageCtx,
    run_evaluation_stage,
)
from packages.application.m12_reference.clean_run_stages import (
    admit_evidence,
    build_audit,
    build_deliverable_payload,
    close_budget,
    collect_usage_summary,
    commit_memory,
    experiment_run_id_of,
    run_artifacts,
)
from packages.application.m12_reference.deps import CleanRunDeps
from packages.application.model_relay.fingerprint import endpoint_config_digest
from packages.application.model_relay.live_probe import run_live_probe
from packages.application.run_orchestration.m12_composition import (
    FallbackFreeze,
    M12CompositionRequest,
    M12ManifestExtras,
    compose_m12_run,
    manifest_anchors,
)
from packages.domain.core import ID, Digest
from packages.domain.experiment_state import ExperimentPlanState, ExperimentRunState
from packages.domain.experiments import ExperimentPlan, ExperimentRun
from packages.domain.manifest import RunManifest
from packages.domain.workers import GPU_RESOURCE_PROFILES

DATASET_PATH = "examples/eval/datasets/m12_research_v1.yaml"
HYPOTHESIS = "hash-embedding+linear classifier beats tfidf on low-resource subset"

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
    audit_status: str | None = None
    audit_digest: str | None = None
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
            "audit_status": self.audit_status,
            "audit_digest": self.audit_digest,
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
    run, experiment_run_id, hypothesis = _run_experiment(
        deps, run_id, experiment_plan_id, experiment_command, experiment_timeout_seconds
    )
    manifest = _with_image_digest(deps, manifest, run)
    return _complete_run(deps, run_id, manifest, run, hypothesis)


def _complete_run(
    deps: CleanRunDeps,
    run_id: str,
    manifest: RunManifest,
    run: ExperimentRun,
    hypothesis: str,
) -> CleanRunResult:
    """manifest 冻结后阶段：evidence→memory→audit→eval→budget→deliverable。"""
    experiment_run_id = str(run.id.value)
    anchors = manifest_anchors(manifest)
    if not anchors["ok"]:
        raise RuntimeError(f"manifest anchors missing: {anchors['missing']}")
    claim_id, evidence_ids, claim_status = admit_evidence(deps, run_id, manifest, run)
    commit_memory(deps, run_id, claim_id)
    audit = build_audit(deps, run_id, run)
    usage_summary = collect_usage_summary(deps, run_id, run)
    eval_ctx = EvalStageCtx(
        audit=audit, claim_id=claim_id, usage_summary=usage_summary, hypothesis=hypothesis
    )
    eval_report = run_evaluation_stage(deps, run_id, eval_ctx)
    budget_summary = close_budget(deps, run_id, run, eval_report)
    deliverable = build_deliverable_payload(deps, run_id, manifest, eval_report, audit)
    deliverable_digest = Digest.of_bytes(
        json.dumps(deliverable, ensure_ascii=False, sort_keys=True).encode("utf-8")
    )
    artifact_ids, artifact_digests = run_artifacts(deps, run_id)
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
        audit_status=audit.status,
        audit_digest=str(audit.audit_digest) if audit.audit_digest else None,
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
        endpoint_config_digest=_endpoint_digest(deps),
        probe_suite_digest=None,
        fallback=FallbackFreeze(),
        evaluation_dataset_digest=_dataset_digest(deps),
    )


def _endpoint_digest(deps: CleanRunDeps) -> str | None:
    return str(endpoint_config_digest(deps.endpoint)) if deps.endpoint else None


def _dataset_digest(deps: CleanRunDeps) -> str:
    from adapters.contracts.eval_loaders import load_eval_dataset

    return str(load_eval_dataset(deps.dataset_path).digest())


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
) -> tuple[ExperimentRun, str, str]:
    """执行真实实验；实验脚本（如提供）先复制进工作区（容器内无仓库）。"""
    experiment_run_id = experiment_run_id_of(run_id)
    session_id = f"session-{run_id[:8]}"
    lease = deps.workspaces.acquire_lease(deps.workspace, session_id)
    plan = ExperimentPlan(
        id=experiment_plan_id,
        name=deps.plan_name,
        hypothesis=deps.hypothesis,
    ).transition(ExperimentPlanState.Transition.PREREGISTER)
    effective_command = _provision_experiment(deps, command, lease)
    environment = {"EXPERIMENT_RUN_ID": experiment_run_id}
    if deps.resource_profile in GPU_RESOURCE_PROFILES:
        # M17 determinism control for cuBLAS on the GPU slice (set BEFORE torch
        # import inside the container; the experiment reads it from env).
        environment["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    executor = ExperimentExecutor(
        execution=deps.execution,
        workspaces=deps.workspaces,
        artifacts=deps.artifacts,
        workspace_dir=_workspace_dir_fn(deps),
    )
    outcome = executor.execute(
        ExperimentExecutionRequest(
            plan=plan,
            run_id=ID(experiment_run_id),
            command=effective_command,
            workspace=deps.workspace,
            agent_session_id=session_id,
            seed=7,
            resource_profile=deps.resource_profile,
            environment=environment,
            timeout_seconds=timeout_seconds,
        )
    )
    if outcome.run.state not in (
        ExperimentRunState.State.SUCCEEDED,
        ExperimentRunState.State.NEGATIVE_RESULT,
    ):
        raise RuntimeError(f"experiment failed: {outcome.run.state}")
    return outcome.run, experiment_run_id, deps.hypothesis


def _provision_experiment(deps: CleanRunDeps, command: str, lease: object) -> str:
    # 容器只挂载工作区（不含仓库源码），脚本需先复制进工作区
    if deps.experiment_script is None:
        return command
    workspace_dir = _workspace_dir_resolver(deps)(lease)
    shutil.copyfile(deps.experiment_script, Path(workspace_dir) / "experiment.py")
    return "python experiment.py"


def _with_image_digest(
    deps: CleanRunDeps,
    manifest: RunManifest,
    run: ExperimentRun,
) -> RunManifest:
    """补冻结真实 image_digest（backend 观测优先；fake 回退 artifact payload）。"""
    image_digest = run.result.image_digest if run.result is not None else None
    if not image_digest:
        artifact_id = f"{run.id.value}:experiment_result.json"
        content = deps.artifacts.get(artifact_id)
        payload = json.loads(content.decode("utf-8"))
        image_digest = payload.get("image_digest")
    if not isinstance(image_digest, str) or not image_digest:
        raise RuntimeError("experiment artifact/image missing image_digest")
    return replace(manifest, image_digest=image_digest)


def _workspace_dir_resolver(deps: CleanRunDeps) -> Callable[[object], Path]:
    # workspace_dir 解析：显式 workspace_root > backend 方法 > 临时目录
    if deps.workspace_root is not None:
        root = Path(str(deps.workspace_root))
        return lambda lease: root
    resolver = getattr(deps.workspaces, "workspace_dir", None)
    if callable(resolver):
        return resolver  # type: ignore[no-any-return]
    import tempfile

    root = Path(tempfile.mkdtemp(prefix="m12-clean-run-"))
    return lambda lease: root


def _workspace_dir_fn(deps: CleanRunDeps) -> Callable[[object], Path]:
    """类型化 workspace_dir 解析（mypy strict 兼容）。"""
    return _workspace_dir_resolver(deps)
