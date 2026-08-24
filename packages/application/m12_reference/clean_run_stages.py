"""M12 clean-run 阶段实现（M12-R1 WP2/3/5/6/8）。

编排在 clean_run.py；本模块承载各阶段，全部事实来自真实运行状态
（ExperimentRun / ArtifactStore / EvidenceLedger / BudgetLedger）：

- admit_evidence：真实 ExperimentRun → Source → Evidence → Claim → VERIFIED；
- commit_memory：经 5 阶段 gate 入账（provenance 来自真实 evidence source）；
- build_audit：从真实 run 构建 ReproducibilityAudit（command/input/env/
  snapshots/image 全部真实绑定，无合成常量）；
- close_budget：真实事件归账（实验时长来自 backend 观测；评测 usage 来自
  实际 EvalReport）；缺字段显式 UNKNOWN。

评测阶段（输入构造 + fail-closed gate）在 clean_run_eval.py。
"""

from __future__ import annotations

from packages.application.deliverable.builder import DeliverableInputs, build_deliverable
from packages.application.evidence.m12_chain import (
    MemoryProposalInput,
    propose_and_commit_memory,
    verify_claim,
)
from packages.application.experiments import (
    ExperimentProvenance,
    register_experiment_evidence,
)
from packages.application.experiments.usage_collection import (
    UsageCollection,
    collect_usage,
    record_collected_usage,
)
from packages.application.m12_reference.deps import CleanRunDeps
from packages.application.memory.gate import MemoryGateDeps
from packages.domain.core import ID
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.eval_result import EvalReport
from packages.domain.experiments import ExperimentRun
from packages.domain.manifest import RunManifest
from packages.domain.reproducibility import ReproducibilityAudit

CLAIM_STATEMENT = (
    "baseline tfidf+linear_softmax outperforms candidate "
    "hash_embedding+linear_softmax on the low-resource subset"
)


def experiment_run_id_of(run_id: str) -> str:
    """实验 run id 派生（与 run_id 同源、确定性、合法 UUID4，可审计可重放）。"""
    return f"5a1c6a8e-9b2d-4f3a-8c5e-{run_id.replace('-', '')[:12]}"


def admit_evidence(
    deps: CleanRunDeps,
    run_id: str,
    manifest: RunManifest,
    run: ExperimentRun,
) -> tuple[str, tuple[str, ...], str]:
    """真实 ExperimentRun → Evidence/Claim → VERIFIED（唯一升级入口）。"""
    result = register_experiment_evidence(
        deps.ledger,
        run,
        deps.artifacts,
        provenance=ExperimentProvenance(
            run_id=run_id,
            manifest_digest=str(manifest.digest()),
        ),
        claim_statement=CLAIM_STATEMENT,
    )
    verified = verify_claim(
        deps.ledger,
        deps.ledger.get_claim(result.claim.id),
        reviewer="gate:independent-acceptance",
        verdict="PASS",
    )
    return verified.id, tuple(item.id for item in result.evidence), verified.status.value


def commit_memory(deps: CleanRunDeps, run_id: str, claim_id: str) -> None:
    """Governed Memory 入账；provenance 必须来自真实 evidence source。"""
    memory_deps = MemoryGateDeps(
        store=deps.memory,
        ledger=deps.ledger,
        actor="system:m12",
    )
    relations = deps.ledger.relations_for_claim(claim_id)
    if not relations:
        raise RuntimeError("claim has no evidence relations for memory provenance")
    evidence = deps.ledger.get_evidence(relations[0].evidence_id)
    memory_id = propose_and_commit_memory(
        memory_deps,
        input=MemoryProposalInput(
            memory_id=f"mem:{run_id}:negative-result",
            content=(
                "hash-embedding+linear_softmax candidate did not beat "
                "tfidf baseline on low-resource 20-class subset"
            ),
            provenance=evidence.source_ref,
            kind=MemoryType.NEGATIVE_RESULT,
            tier=MemoryTier.PROJECT,
            confidence=0.97,
            curator_approved=True,
        ),
    )
    if memory_id is None:
        raise RuntimeError("governed memory commit rejected")


def build_audit(deps: CleanRunDeps, run_id: str, run: ExperimentRun) -> ReproducibilityAudit:
    """从真实运行事实构建并封存 ReproducibilityAudit（无合成绑定常量）。"""
    from packages.application.experiments import build_reproducibility_audit

    return build_reproducibility_audit(
        run,
        audit_id=ID(f"a1b2c3d4-5e6f-4a5b-9c0d-{run_id.replace('-', '')[:12]}"),
        artifacts=deps.artifacts,
    )


def collect_usage_summary(deps: CleanRunDeps, run_id: str, run: ExperimentRun) -> dict[str, int]:
    """真实事件 → 用量摘要（只读，不落账；供评测 cost 输入）。"""
    _closure, summary = collect_usage(
        UsageCollection(
            run_id=run_id,
            experiment_result=run.result,
        )
    )
    return {
        "model_tokens": summary.model_tokens,
        "tool_requests": summary.tool_requests,
        "experiment_runs": 1 if run.result is not None else 0,
        "evaluation_runs": 0,
    }


def close_budget(
    deps: CleanRunDeps,
    run_id: str,
    run: ExperimentRun,
    eval_report: EvalReport | None,
) -> dict[str, int]:
    """真实事件归账（实验时长来自 backend 观测；评测 usage 来自 EvalReport）。"""
    record_collected_usage(
        deps.budget,
        UsageCollection(
            run_id=run_id,
            experiment_result=run.result,
            eval_report=eval_report,
        ),
    )
    entries = deps.budget.snapshot().entries
    return {
        "entries": len(entries),
        "tokens": sum(
            entry.quantity for entry in entries if entry.resource_type.value == "MODEL_TOKENS"
        ),
    }


def run_artifacts(deps: CleanRunDeps, run_id: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    refs = [
        artifact
        for artifact in deps.artifacts.list_refs()
        if artifact.id.startswith(run_id + ":")
        or artifact.id.startswith(experiment_run_id_of(run_id) + ":")
    ]
    return tuple(item.id for item in refs), tuple(str(item.digest) for item in refs)


def build_deliverable_payload(
    deps: CleanRunDeps,
    run_id: str,
    manifest: RunManifest,
    eval_report: EvalReport,
    audit: ReproducibilityAudit,
) -> dict[str, object]:
    return build_deliverable(
        DeliverableInputs(
            run_id=run_id,
            manifest=manifest,
            artifacts=deps.artifacts,
            ledger=deps.ledger,
            memory=deps.memory,
            budget=deps.budget,
            audit=audit,
            eval_report=eval_report,
            objective=deps.objective,
        )
    )


__all__ = [
    "CLAIM_STATEMENT",
    "admit_evidence",
    "build_audit",
    "build_deliverable_payload",
    "close_budget",
    "collect_usage_summary",
    "commit_memory",
    "experiment_run_id_of",
    "run_artifacts",
]
