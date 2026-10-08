"""Experiment 控制面（M13-R1 WP-S4 + PLAN-20260910-037 WP-E）。

从 persisted truth 聚合 run 的 experiment 信息：
- evidence 行含 experiment_run_id → 可关联 experiment run + artifact；
- metrics 经 ArtifactStore 内容寻址读取（若内容可取得）；
- Reproduction：M12 chain 的 ReproducibilityAudit 不在控制面板存储边界内，
  诚实标注 unavailable（不伪造审计 digest）；file-level workspace diff
  自 PLAN-20260915-058 起由 /workspace-snapshots 提供（见 REPRODUCTION_NOTE）。

WP-E 新增：项目级 run 视图（跨 run evidence 聚合）、ExperimentPlan 预注册
创建与归档。PLAN-040 WP-A 起 SQLite 开发路径与 PG canonical 双支持；store
未配置仍诚实 503。G14（PLAN-052）起队列/调度由独立路由
（`services/api/routers/experiment_queue.py`）+ 控制面派发器承载：计划状态本身
仍只有 DRAFT/PREREGISTERED/ARCHIVED（排队事实在队列条目上，不写进计划状态），
执行归属由 run 证据呈现。
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Request

from packages.application.experiments.repro_audit import (
    verify_audit_outputs,
    verify_reproducibility_audit,
)
from packages.application.ports import EvidenceLedger
from packages.domain.core import ID
from packages.domain.evidence import Evidence
from packages.domain.experiment_state import ExperimentPlanState
from packages.domain.experiments import ExperimentPlan
from packages.domain.run import ResearchRun
from packages.domain.state_base import InvalidTransitionError
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.experiments import (
    ExperimentPlanCreateDto,
    ExperimentPlanDto,
    ExperimentRunRowDto,
    ProjectExperimentsViewDto,
)
from services.api.dto.inspection import (
    AuditFindingDto,
    ExperimentRunDto,
    ExperimentViewDto,
)
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
        _apply_audit(deps, experiment)
    return ExperimentViewDto(
        experiments=experiments,
        reproduction_note=reproduction_note(experiments),
    )


REPRODUCTION_NOTE = (
    "**没有审计的实验**：honest unavailable —— 本视图不推测复现性（GOAL-20261008-035 EC-02 "
    "起，研究循环 run 路径会为终态实验落一份 ReproducibilityAudit，读面逐条给出 "
    "audit_digest / audit_status / audit_verified / audit_findings）。工作区快照的"
    "**文件级** diff 由 GET /workspace-snapshots/{left}/diff/{right} 提供（PLAN-20260915-058）"
)
AUDITED_NOTE = (
    "复现结论来自**已落库**的 ReproducibilityAudit（run 路径在实验终态时产出）："
    "audit_verified 是**重算封存 digest** 的结果（漂移/篡改检测），audit_findings 逐条"
    "给出发现（缺失锚点 / 制品缺失 / 内容损坏 / digest 漂移，**逐条点名**）。"
    "**边界**：本口径只声明「可重复配置」，不声明位级复现。"
)


def reproduction_note(experiments: list[ExperimentRunDto]) -> str:
    """按**事实**选措辞：视图里有审计 ⇒ 谈读数；没有 ⇒ 诚实 unavailable。"""
    if any(item.reproduction_available for item in experiments):
        return AUDITED_NOTE
    return REPRODUCTION_NOTE


def _apply_audit(deps: ApiDeps, experiment: ExperimentRunDto) -> None:
    """把**存储里**的审计读数贴到 DTO 上（没有审计 ⇒ 三个字段保持缺席）。

    `audit_verified` 由**重算**得出（`verify_reproducibility_audit`），不是回读一个标记；
    跨核对的发现（`verify_audit_outputs`）与锚点发现合并进 `audit_findings`。
    """
    store = deps.experiment_store
    if store is None:
        return
    try:
        audit = store.get_audit(experiment.experiment_run_id)
    except Exception:  # noqa: BLE001 - 没有该实验的审计（读面如实缺席）
        return
    findings = [
        AuditFindingDto(code=item.code, severity=item.severity, message=item.message)
        for item in audit.findings()
    ]
    findings.extend(_output_findings(deps, audit))
    experiment.reproduction_available = True
    experiment.audit_digest = None if audit.audit_digest is None else str(audit.audit_digest)
    experiment.audit_status = audit.status
    experiment.audit_verified = verify_reproducibility_audit(audit)
    experiment.audit_findings = findings


def _output_findings(deps: ApiDeps, audit: Any) -> list[AuditFindingDto]:
    """把审计绑定的输出 digest 与制品存储**当前内容**交叉核对（点名出问题的制品）。"""
    store = deps.experiment_store
    artifacts = deps.artifacts
    if store is None or artifacts is None:
        return []
    try:
        run = store.get_run(audit.experiment_run_id.value)
    except Exception:  # noqa: BLE001 - 实验行不在（只有审计）⇒ 跳过交叉核对
        return []
    return [
        AuditFindingDto(code=item.code, severity=item.severity, message=item.message)
        for item in verify_audit_outputs(audit, run, artifacts)
    ]


def _project_runs(deps: ApiDeps, project_id: str) -> list[ResearchRun]:
    if deps.runs_store is not None:
        return list(deps.runs_store.list_runs(project_id))
    return [run for run in deps.run_registry.values() if run.project_id == project_id]


@router.get("/projects/{project_id}/experiments", response_model=ProjectExperimentsViewDto)
async def project_experiments(project_id: str, request: Request) -> ProjectExperimentsViewDto:
    """项目级 experiment run 视图（跨 run 的 evidence 聚合；WP-E）。"""
    deps: ApiDeps = get_deps(request)
    if deps.ledger is None:
        raise ApiError(503, "Evidence Ledger Unavailable", "evidence ledger not configured")
    rows: list[ExperimentRunRowDto] = []
    for run in _project_runs(deps, project_id):
        for experiment in _experiments_of_run(deps.ledger, run.id.value):
            _enrich_metrics(deps, experiment)
            rows.append(ExperimentRunRowDto(run_id=run.id.value, **experiment.model_dump()))
    return ProjectExperimentsViewDto(experiments=rows, reproduction_note=REPRODUCTION_NOTE)


def _enrich_metrics(deps: ApiDeps, experiment: ExperimentRunDto) -> None:
    for artifact_id in experiment.artifact_ids:
        metrics = _metrics_for(deps, artifact_id)
        if metrics:
            experiment.metrics = {**experiment.metrics, **metrics}


def _store_of(deps: ApiDeps) -> object:
    if deps.experiment_store is None:
        raise ApiError(
            503,
            "Experiment Store Unavailable",
            "experiment store not configured",
        )
    return deps.experiment_store


def _plan_dto(plan: ExperimentPlan) -> ExperimentPlanDto:
    return ExperimentPlanDto(
        id=plan.id.value,
        name=plan.name,
        hypothesis=plan.hypothesis,
        task_contract_ref=plan.task_contract_ref,
        input_spec_digest=str(plan.input_spec_digest) if plan.input_spec_digest else None,
        state=plan.state,
        created_at=plan.created_at.value.isoformat(),
        updated_at=plan.updated_at.value.isoformat(),
    )


@router.post(
    "/projects/{project_id}/experiments",
    response_model=ExperimentPlanDto,
    status_code=201,
)
async def create_experiment_plan(
    project_id: str, payload: ExperimentPlanCreateDto, request: Request
) -> ExperimentPlanDto:
    """预注册实验计划（DRAFT→PREREGISTERED 持久化；无队列语义，不伪装 queued）。"""
    del project_id
    deps: ApiDeps = get_deps(request)
    store = _store_of(deps)
    plan = ExperimentPlan(
        id=ID.generate(),
        name=payload.name,
        hypothesis=payload.hypothesis,
        task_contract_ref=payload.task_contract_ref,
    ).transition(ExperimentPlanState.Transition.PREREGISTER)
    store.save_plan(plan)  # type: ignore[attr-defined]
    return _plan_dto(plan)


@router.post("/experiments/{plan_id}/archive", response_model=ExperimentPlanDto)
async def archive_experiment_plan(plan_id: str, request: Request) -> ExperimentPlanDto:
    """归档计划（域状态机权威：已归档/非法迁移 → 409；未知 → 404）。"""
    deps: ApiDeps = get_deps(request)
    store = _store_of(deps)
    try:
        plan = store.get_plan(plan_id)  # type: ignore[attr-defined]
    except Exception as exc:  # noqa: BLE001 - InvalidInputError 统一映射 404
        raise ApiError(404, "Experiment Plan Not Found", f"unknown plan id: {plan_id}") from exc
    try:
        archived = plan.transition(ExperimentPlanState.Transition.ARCHIVE)
    except InvalidTransitionError as exc:
        raise ApiError(409, "Invalid Transition", str(exc)) from exc
    store.save_plan(archived)  # type: ignore[attr-defined]
    return _plan_dto(archived)
