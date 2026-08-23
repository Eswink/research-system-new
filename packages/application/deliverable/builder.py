"""M12 Deliverable 只读聚合器（M12-R1 WP3）。

Report builder 只能 render truth，不能创造 scientific truth：
- 输入是 run_id 与正式持久状态（ArtifactStore / EvidenceLedger / MemoryStore /
  BudgetLedger / ReproducibilityAudit / EvalReport / RunManifest）；
- 报告的 numbers / digests / source ids / claim status / eval verdict /
  reproduction / budget 全部 SELECT 自持久状态，禁止代码内常量；
- 任何读取失败（artifact 缺失 / digest 校验失败 / claim 不存在）→ 明确报错，
  不得 fallback 到合成值。

本模块只做只读聚合；写入（实验、证据、记忆、账本）由各自生产 use case 完成。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.budget_ledger import BudgetLedger
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.application.ports.memory_store import MemoryStore
from packages.domain.core import Digest
from packages.domain.eval_result import EvalReport
from packages.domain.evidence import Claim, ClaimStatus
from packages.domain.manifest import RunManifest
from packages.domain.reproducibility import ReproducibilityAudit


@dataclass(frozen=True, slots=True)
class DeliverableInputs:
    """Deliverable 的全部正式输入（参数对象，避免函数参数超限）。"""

    run_id: str
    manifest: RunManifest
    artifacts: ArtifactStore
    ledger: EvidenceLedger
    memory: MemoryStore
    budget: BudgetLedger
    audit: ReproducibilityAudit | None = None
    eval_report: EvalReport | None = None
    objective: str | None = None


class DeliverableBuildError(RuntimeError):
    """Deliverable 无法从正式状态构造（输入缺失/不一致），不是可静默降级的情况。"""


def build_deliverable(inputs: DeliverableInputs) -> dict[str, object]:
    """从持久状态聚合 M12 research report（只读；任何缺失即失败）。"""
    experiment = _experiment_block(inputs)
    evidence_block = _evidence_block(inputs)
    memory_block = _memory_block(inputs)
    budget_block = _budget_block(inputs)
    evaluation_block = _evaluation_block(inputs)
    reproduction_block = _reproduction_block(inputs)
    return {
        "report_id": f"m12-reference-research:{inputs.run_id}",
        "run_id": inputs.run_id,
        "objective": inputs.objective or "",
        "protocol": {
            "id": (
                inputs.manifest.protocol_digest.hex_value[:16]
                if inputs.manifest.protocol_digest
                else "unknown"
            ),
            "version": inputs.manifest.protocol_version.text,
            "protocol_digest": (
                str(inputs.manifest.protocol_digest) if inputs.manifest.protocol_digest else None
            ),
            "compiled_plan_digest": (
                str(inputs.manifest.compiled_plan_digest)
                if inputs.manifest.compiled_plan_digest
                else None
            ),
            "manifest_digest": str(inputs.manifest.digest()),
            "semantic_digest": str(inputs.manifest.semantic_digest()),
        },
        "experiment": experiment,
        "evidence_chain": evidence_block,
        "memory": memory_block,
        "budget": budget_block,
        "evaluation": evaluation_block,
        "reproduction": reproduction_block,
    }


def _experiment_block(inputs: DeliverableInputs) -> dict[str, object]:
    """实验块：artifact 引用来自 Claim 的真实 evidence（内容寻址校验）。"""
    artifact_id = _experiment_artifact_id(inputs)
    content = _get_artifact_content(inputs.artifacts, artifact_id)
    import json

    payload = json.loads(content.decode("utf-8"))
    if not isinstance(payload, dict):
        raise DeliverableBuildError("experiment artifact is not a JSON object")
    metrics = payload.get("metrics")
    if not isinstance(metrics, dict):
        raise DeliverableBuildError("experiment artifact missing metrics object")
    digest = Digest.of_bytes(content)
    return {
        "artifact_id": artifact_id,
        "artifact_digest": str(digest),
        "experiment_run_id": payload.get("experiment_run_id", ""),
        "status": payload.get("status", ""),
        "seed": payload.get("seed"),
        "metrics": _stringify(metrics),
        "raw_artifact_digest": str(digest),
        "semantic_metrics_digest": _semantic_digest_str(inputs),
    }


def _experiment_artifact_id(inputs: DeliverableInputs) -> str:
    """实验 artifact id 来自 Claim 的 evidence 绑定（真实持久状态，非硬编码）。"""
    claim = _claim_for_run(inputs)
    relations = inputs.ledger.relations_for_claim(claim.id)
    for relation in relations:
        evidence = inputs.ledger.get_evidence(relation.evidence_id)
        if evidence.artifact_id and evidence.artifact_id.endswith("experiment_result.json"):
            return evidence.artifact_id
    return f"{inputs.run_id}:experiment_result.json"


def _claim_for_run(inputs: DeliverableInputs) -> Claim:
    """从 ledger 中查找属于当前 run 的 claim（claim id 由 admission 派生）。"""
    claims = inputs.ledger.claims()
    for claim in claims:
        relations = inputs.ledger.relations_for_claim(claim.id)
        for relation in relations:
            evidence = inputs.ledger.get_evidence(relation.evidence_id)
            if evidence.run_id == inputs.run_id:
                return claim
    raise DeliverableBuildError(f"no claim found for run {inputs.run_id}")


def _semantic_digest_str(inputs: DeliverableInputs) -> str | None:
    if inputs.audit is not None and inputs.audit.semantic_metrics_digest is not None:
        return str(inputs.audit.semantic_metrics_digest)
    if inputs.audit is not None and inputs.audit.metrics_digest is not None:
        return str(inputs.audit.metrics_digest)
    return None


def _evidence_block(inputs: DeliverableInputs) -> dict[str, object]:
    claim = _claim_for_run(inputs)
    claim_id = claim.id
    relations = inputs.ledger.relations_for_claim(claim_id)
    evidence_ids = tuple(relation.evidence_id for relation in relations)
    sources: dict[str, str] = {}
    for relation in relations:
        evidence = inputs.ledger.get_evidence(relation.evidence_id)
        source = inputs.ledger.get_source(evidence.source_ref)
        sources[evidence.id] = source.origin
    return {
        "claim_id": claim.id,
        "claim_status": claim.status.value,
        "evidence_ids": evidence_ids,
        "relation_types": tuple(relation.relation.value for relation in relations),
        "evidence_sources": sources,
        "is_verified": claim.status is ClaimStatus.VERIFIED,
    }


def _memory_block(inputs: DeliverableInputs) -> dict[str, object]:
    memory_id = f"mem:{inputs.run_id}:negative-result"
    try:
        record = inputs.memory.get(memory_id)
    except Exception as exc:  # noqa: BLE001 - Port 故障 = 状态不完整
        raise DeliverableBuildError(f"memory {memory_id} unavailable: {exc}") from exc
    return {
        "memory_id": record.id,
        "kind": record.kind.value,
        "tier": record.tier.value,
        "provenance": record.provenance,
        "confidence": record.confidence,
        "active": record.active,
    }


def _budget_block(inputs: DeliverableInputs) -> dict[str, object]:
    snapshot = inputs.budget.snapshot()
    total_tokens = 0
    tool_requests = 0
    experiment_runs = 0
    for entry in snapshot.entries:
        if entry.resource_type.value == "MODEL_TOKENS":
            total_tokens += entry.quantity
        elif entry.resource_type.value == "TOOL_REQUESTS":
            tool_requests += entry.quantity
        elif entry.resource_type.value == "CPU_TIME":
            experiment_runs += 1
    return {
        "total_model_tokens": total_tokens,
        "tool_requests": tool_requests,
        "experiment_runs": experiment_runs,
        "entries": len(snapshot.entries),
        "reservations": len(snapshot.reservations),
        "ledger_entries": [
            {
                "entry_id": entry.entry_id,
                "resource_type": entry.resource_type.value,
                "quantity": entry.quantity,
                "unit": entry.unit,
                "cost_status": entry.cost_status.value,
            }
            for entry in snapshot.entries
        ],
    }


def _evaluation_block(inputs: DeliverableInputs) -> dict[str, object]:
    report = inputs.eval_report
    if report is None:
        raise DeliverableBuildError("eval report not provided; evaluation not run")
    frozen = report.frozen_conditions
    return {
        "dataset": frozen.dataset_id,
        "dataset_digest": str(frozen.dataset_digest),
        "mode": report.mode,
        "verdict": report.gate_verdict.value,
        "case_count": len(report.results),
    }


def _reproduction_block(inputs: DeliverableInputs) -> dict[str, object]:
    audit = inputs.audit
    if audit is None:
        raise DeliverableBuildError("reproducibility audit not provided")
    return {
        "audit_id": str(audit.audit_id.value),
        "audit_status": audit.status,
        "audit_digest": str(audit.audit_digest) if audit.audit_digest else None,
        "metrics_digest": str(audit.metrics_digest) if audit.metrics_digest else None,
        "semantic_metrics_digest": (
            str(audit.semantic_metrics_digest) if audit.semantic_metrics_digest else None
        ),
        "observational_metrics_digest": (
            str(audit.observational_metrics_digest)
            if audit.observational_metrics_digest
            else None
        ),
        "image_digest": audit.image_digest,
        "seed": audit.seed,
        "output_artifact_digests": list(audit.output_artifact_digests),
    }


def _get_artifact_content(artifacts: ArtifactStore, artifact_id: str) -> bytes:
    try:
        content = artifacts.get(artifact_id)
    except Exception as exc:  # noqa: BLE001 - Port 故障 = 状态不完整
        raise DeliverableBuildError(
            f"artifact {artifact_id} unavailable: {exc}"
        ) from exc
    return content


def _stringify(metrics: Mapping[str, object]) -> dict[str, str]:
    return {str(key): str(value) for key, value in metrics.items()}


__all__ = ["DeliverableBuildError", "DeliverableInputs", "build_deliverable"]