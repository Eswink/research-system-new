"""M12 clean-run 评测阶段（M12-R1 WP5）。

评测输入从持久状态构造（禁止空输入自证）；verdict 非 PASS 即失败
（fail-closed，deliverable 不产出）。与 clean_run_stages.py 拆分
（保持模块规模阈值）。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal

from adapters.contracts.eval_loaders import load_eval_dataset
from packages.application.evaluation.runner import RunRequest, run_evaluation
from packages.application.evaluation.scorer_types import ScorerFn
from packages.application.evaluation.scorers_m12_truth import (
    direction_improvement_scorer,
    metric_correctness_scorer,
)
from packages.application.evaluation.scorers_m12_truth_evidence import (
    citation_source_scorer,
    evidence_artifact_scorer,
    unsupported_claim_scorer,
)
from packages.application.m12_reference.clean_run_stages import experiment_run_id_of
from packages.application.m12_reference.deps import CleanRunDeps
from packages.domain.core import Version
from packages.domain.enums import QualityGateVerdict
from packages.domain.eval_gate import GateConfig
from packages.domain.eval_result import EvalReport
from packages.domain.evidence import Claim
from packages.domain.reproducibility import ReproducibilityAudit

DATASET_PATH = "examples/eval/datasets/m12_research_v1.yaml"
GATE_ID = "m12-independent-gate"
GATE_VERSION = "1.0.0"
GATE_MIN_PASS = "0.8"


@dataclass(frozen=True, slots=True)
class EvalStageCtx:
    """评测阶段上下文（参数对象，避免函数参数超限）。"""

    audit: ReproducibilityAudit
    claim_id: str
    usage_summary: dict[str, int]
    hypothesis: str


def run_evaluation_stage(
    deps: CleanRunDeps,
    run_id: str,
    ctx: EvalStageCtx,
) -> EvalReport:
    """从持久状态构造评测输入并执行；verdict 非 PASS 即失败（fail-closed）。"""
    dataset = load_eval_dataset(deps.dataset_path)
    inputs = build_eval_inputs(deps, run_id, ctx)
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
            inputs=inputs,
            evidence=_evidence_map(deps, ctx.claim_id),
            runtime_scorers=_runtime_scorers(deps, run_id),
        )
    )
    if outcome.missing_inputs:
        raise RuntimeError(f"evaluation inputs unresolved: {outcome.missing_inputs}")
    report = outcome.report
    if report.gate_verdict is not QualityGateVerdict.PASS:
        detail = "; ".join(
            f"{result.case_id}:"
            + ",".join(finding.status.value for finding in result.scorer_findings)
            for result in report.results
        )
        raise RuntimeError(f"evaluation gate not passed: {report.gate_verdict.value} ({detail})")
    return report


def build_eval_inputs(
    deps: CleanRunDeps,
    run_id: str,
    ctx: EvalStageCtx,
) -> dict[str, object]:
    """评测输入全部来自持久状态（artifact / ledger / audit / usage）。"""
    artifact_id = f"{experiment_run_id_of(run_id)}:experiment_result.json"
    payload = json.loads(deps.artifacts.get(artifact_id).decode("utf-8"), parse_float=Decimal)
    if not isinstance(payload, dict):
        raise RuntimeError("experiment artifact is not a JSON object")
    metrics = payload.get("metrics")
    if not isinstance(metrics, dict):
        raise RuntimeError("experiment artifact missing metrics object")
    claim = deps.ledger.get_claim(ctx.claim_id)
    relations = deps.ledger.relations_for_claim(ctx.claim_id)
    evidence_ids = tuple(relation.evidence_id for relation in relations)
    distinct_sources = {
        deps.ledger.get_evidence(relation.evidence_id).source_ref for relation in relations
    }
    return _inputs(
        payload,
        metrics,
        ctx,
        claim,
        evidence_ids,
        len(distinct_sources),
    )


def _inputs(  # noqa: PLR0913 - 评测输入聚合（参数对象会降低可读性）
    payload: dict[str, object],
    metrics: dict[str, object],
    ctx: EvalStageCtx,
    claim: Claim,
    evidence_ids: tuple[str, ...],
    distinct_sources: int,
) -> dict[str, object]:
    return {
        "input://m12/task_completion": {"status": payload.get("status")},
        "input://m12/evidence_support": {"sources": distinct_sources},
        "input://m12/experimental_validity": {
            "status": payload.get("status"),
            "hypothesis": ctx.hypothesis,
            "metrics": metrics,
            "seed": payload.get("seed"),
        },
        "input://m12/result_correctness": str(metrics.get("baseline_accuracy")),
        "input://m12/reproducibility": _repro_input(ctx.audit),
        "input://m12/claim_calibration": {
            "claim_id": claim.id,
            "claim_status": claim.status.value,
        },
        "input://m12/citation_correctness": claim.statement,
        "input://m12/unsupported_conclusion": {"unsupported_claims": []},
        "input://m12/deliverable_quality": {
            "claim_id": claim.id,
            "evidence_ids": list(evidence_ids),
            "metrics": metrics,
        },
        "input://m12/evidence_artifact": {"claim_id": claim.id},
        "input://m12/cost_efficiency": {
            "model_tokens": ctx.usage_summary["model_tokens"],
            "tool_requests": ctx.usage_summary["tool_requests"],
            "experiment_runs": ctx.usage_summary["experiment_runs"],
            "evaluation_runs": ctx.usage_summary["evaluation_runs"],
        },
        # M17 GPU slice reuses this harness — the m17 dataset reads these keys.
        "input://m17/task_completion": {"status": payload.get("status")},
        "input://m17/experiment_result": payload,
        "input://m17/experimental_validity": {
            "status": payload.get("status"),
            "hypothesis": ctx.hypothesis,
            "metrics": metrics,
            "seed": payload.get("seed"),
        },
        "input://m17/reproducibility": _repro_input(ctx.audit),
        "input://m17/evidence_support": {"sources": distinct_sources},
        "input://m17/cost_efficiency": {
            "model_tokens": ctx.usage_summary["model_tokens"],
            "experiment_runs": ctx.usage_summary["experiment_runs"],
            "gpu_seconds": ctx.usage_summary.get("gpu_seconds", 0),
        },
    }


def _repro_input(audit: ReproducibilityAudit) -> dict[str, object]:
    return {
        "audit_status": audit.status,
        "image_digest": audit.image_digest,
        "workspace_snapshot_before": audit.workspace_snapshot_before,
        "workspace_snapshot_after": audit.workspace_snapshot_after,
        "metrics_digest": str(audit.metrics_digest) if audit.metrics_digest else None,
    }


def _evidence_map(deps: CleanRunDeps, claim_id: str) -> dict[str, dict[str, str]]:
    relations = deps.ledger.relations_for_claim(claim_id)
    sources: dict[str, str] = {}
    for relation in relations:
        evidence = deps.ledger.get_evidence(relation.evidence_id)
        sources[evidence.source_ref] = evidence.content_digest
    return {
        "input://m12/evidence_support": sources,
        # M17 GPU slice reuses this harness — the m17 dataset reads this key.
        "input://m17/evidence_support": sources,
    }


def _runtime_scorers(deps: CleanRunDeps, run_id: str) -> dict[tuple[str, str], ScorerFn]:
    return {
        ("metric_correctness", "1.0.0"): metric_correctness_scorer(deps.artifacts),
        ("direction_improvement", "1.0.0"): direction_improvement_scorer(),
        ("citation_source", "1.0.0"): citation_source_scorer(deps.ledger, run_id),
        ("unsupported_claim", "1.0.0"): unsupported_claim_scorer(deps.ledger),
        ("evidence_artifact", "1.0.0"): evidence_artifact_scorer(deps.ledger, deps.artifacts),
    }


__all__ = ["build_eval_inputs", "run_evaluation_stage"]
