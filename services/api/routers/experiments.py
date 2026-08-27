"""Experiment 只读视图（M13-R1 WP-S4）。

从 persisted truth 聚合 run 的 experiment 信息：
- evidence 行含 experiment_run_id → 可关联 experiment run + artifact；
- metrics 经 ArtifactStore 内容寻址读取（若内容可取得）；
- Reproduction：M12 chain 的 ReproducibilityAudit 不在控制面板存储边界内，
  诚实标注 unavailable（不伪造审计 digest），file-level workspace diff
  为 M6/M9 前置能力属性，同样诚实标注。

页面只 render persisted truth；不提供任何 experiment 状态 mutating 通道。
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Request

from packages.application.ports import EvidenceLedger
from packages.domain.evidence import Evidence
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.inspection import ExperimentRunDto, ExperimentViewDto
from services.api.errors import ApiError
from services.api.run_access import get_run_or_error

router = APIRouter(tags=["inspection"])


def _evidence_for_run(ledger: EvidenceLedger, run_id: str) -> list[Evidence]:
    found: list[Evidence] = []
    seen: set[str] = set()
    for claim in ledger.claims():
        for relation in ledger.relations_for_claim(claim.id):
            if relation.evidence_id in seen:
                continue
            seen.add(relation.evidence_id)
            try:
                evidence = ledger.get_evidence(relation.evidence_id)
            except Exception:  # noqa: BLE001 - deleted reference（视觉态：missing evidence）
                continue
            if evidence.run_id == run_id:
                found.append(evidence)
    return found


def _experiments_of_run(ledger: EvidenceLedger, run_id: str) -> list[ExperimentRunDto]:
    experiments: dict[str, ExperimentRunDto] = {}
    for evidence in _evidence_for_run(ledger, run_id):
        if evidence.experiment_run_id is None:
            continue
        key = evidence.experiment_run_id
        experiment = experiments.get(key)
        if experiment is None:
            experiment = ExperimentRunDto(
                experiment_run_id=key,
                artifact_ids=[],
                image_digest=evidence.image_digest,
                environment_digest=evidence.environment_digest,
                metrics={},
                reproduction_available=False,
            )
            experiments[key] = experiment
        if evidence.artifact_id is not None:
            experiment.artifact_ids.append(evidence.artifact_id)
    return list(experiments.values())


def _metrics_for(deps: ApiDeps, artifact_id: str) -> dict[str, object]:
    """artifact 内容寻址读取 metrics（若可取；缺失/非 JSON 按不可得处理）。"""
    if deps.artifacts is None:
        return {}
    try:
        raw = deps.artifacts.get(artifact_id)
        payload = json.loads(raw.decode("utf-8"))
    except Exception:  # noqa: BLE001 - 内容缺失/非 JSON 时视为 metrics 不可得
        return {}
    metrics = payload.get("metrics") if isinstance(payload, dict) else None
    return dict(metrics) if isinstance(metrics, dict) else {}


@router.get("/runs/{run_id}/experiments", response_model=ExperimentViewDto)
async def run_experiments(run_id: str, request: Request) -> ExperimentViewDto:
    """Experiment 视图（persisted truth；reproduction 诚实 unavailable 标注）。"""
    deps: ApiDeps = get_deps(request)
    get_run_or_error(deps, run_id)
    if deps.ledger is None:
        raise ApiError(503, "Evidence Ledger Unavailable", "evidence ledger not configured")
    experiments = _experiments_of_run(deps.ledger, run_id)
    for experiment in experiments:
        for artifact_id in experiment.artifact_ids:
            metrics = _metrics_for(deps, artifact_id)
            if metrics:
                experiment.metrics = {**experiment.metrics, **metrics}
    return ExperimentViewDto(
        experiments=experiments,
        reproduction_note=(
            "ReproducibilityAudit 由 M12 参考链产出，不在控制面板持久化边界内；"
            "file-level workspace diff 为 M6/M9 前置能力，均诚实标注 unavailable"
        ),
    )
