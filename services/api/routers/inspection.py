"""Evidence / Claim / Budget / Audit 只读控制面路由。

页面只 render M10 persisted truth（EvidenceLedger 持久化）；
Claim 状态改变必须经过正式 use case/gate（本层只读，无 UI click → VERIFIED）。
Budget/Usage 来自正式 UsageLedger（KNOWN/UNKNOWN 区分，UNKNOWN ≠ 0）。
Audit/Export 来自 persisted state（内容寻址重算），不导出 UI 内存。
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from packages.application.ports import EvidenceLedger
from packages.domain.budget import LedgerCostStatus
from packages.domain.evidence import Claim, Evidence, EvidenceRelation
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.inspection import (
    BudgetViewDto,
    ClaimDto,
    ClaimMapDto,
    EvidenceDto,
    ExportBundleDto,
    RelationDto,
    UsageEntryDto,
)
from services.api.errors import ApiError
from services.api.run_access import get_run_or_error

router = APIRouter(tags=["inspection"])


def _ledger_of(deps: ApiDeps) -> EvidenceLedger:
    if deps.ledger is None:
        raise ApiError(503, "Evidence Ledger Unavailable", "evidence ledger not configured")
    return deps.ledger


def _evidence_dto(evidence: Evidence) -> EvidenceDto:
    return EvidenceDto(
        id=evidence.id,
        source_ref=evidence.source_ref,
        content_digest=evidence.content_digest,
        run_id=evidence.run_id,
        experiment_run_id=evidence.experiment_run_id,
        artifact_id=evidence.artifact_id,
        image_digest=evidence.image_digest,
        environment_digest=evidence.environment_digest,
        workspace_snapshot_before=evidence.workspace_snapshot_before,
        workspace_snapshot_after=evidence.workspace_snapshot_after,
        model_refs=list(evidence.model_refs),
        manifest_digest=evidence.manifest_digest,
    )


def _relation_dto(relation: EvidenceRelation) -> RelationDto:
    return RelationDto(
        claim_id=relation.claim_id,
        evidence_id=relation.evidence_id,
        relation=relation.relation.value,
        strength=relation.strength,
    )


def _claim_dto(claim: Claim, relations: tuple[EvidenceRelation, ...]) -> ClaimDto:
    return ClaimDto(
        id=claim.id,
        statement=claim.statement,
        status=claim.status.value,
        author=claim.author,
        relations=[_relation_dto(relation) for relation in relations],
    )


def _evidence_of_run(ledger: EvidenceLedger, run_id: str) -> tuple[Evidence, ...]:
    """从 ledger 查询 run 的 evidence（经 relations_for_claim 投影）。"""
    found: list[Evidence] = []
    seen: set[str] = set()
    for claim in ledger.claims():
        for relation in ledger.relations_for_claim(claim.id):
            evidence_id = relation.evidence_id
            if evidence_id in seen:
                continue
            seen.add(evidence_id)
            try:
                evidence = ledger.get_evidence(evidence_id)
            except Exception:  # noqa: BLE001 - 引用可能已删除（视觉态：missing evidence）
                continue
            if evidence.run_id == run_id:
                found.append(evidence)
    return tuple(found)


def _claim_map_for_run(
    ledger: EvidenceLedger, run_id: str
) -> tuple[list[ClaimDto], list[str], list[str]]:
    """run 级 claim map：只保留 relation 命中该 run evidence 的 claim。

    M13-R1（WP-M3，复审实测跨 run 泄漏修复）：此前遍历全量 ledger.claims()
    且不按 run 过滤。现在先取该 run 的 evidence id 集合，只返回 relation
    命中该集合的 claim（relation 展示同样只保留 run 内部分，不泄漏他 run
    evidence 引用）；无任何 relation 的 claim 无法归属 run，不返回。
    """
    run_evidence_ids = {item.id for item in _evidence_of_run(ledger, run_id)}
    claims: list[ClaimDto] = []
    unsupported: list[str] = []
    contradictions: list[str] = []
    for claim in ledger.claims():
        relations = ledger.relations_for_claim(claim.id)
        scoped = tuple(
            relation for relation in relations if relation.evidence_id in run_evidence_ids
        )
        if not scoped:
            continue
        claims.append(_claim_dto(claim, scoped))
        types = {relation.relation for relation in scoped}
        if "SUPPORTS" in types and "REFUTES" in types:
            contradictions.append(claim.id)
    return claims, unsupported, contradictions


@router.get("/runs/{run_id}/evidence", response_model=list[EvidenceDto])
async def run_evidence(run_id: str, request: Request) -> list[EvidenceDto]:
    """run 的 evidence（persisted truth；页面只 render）。"""
    deps: ApiDeps = get_deps(request)
    ledger = _ledger_of(deps)
    return [_evidence_dto(item) for item in _evidence_of_run(ledger, run_id)]


@router.get("/runs/{run_id}/claims", response_model=ClaimMapDto)
async def run_claim_map(run_id: str, request: Request) -> ClaimMapDto:
    """Source → Evidence → Relation → Claim 地图（persisted truth；run 级隔离）。

    视觉语义：contradiction（同一 claim 的 SUPPORTS 与 REFUTES 并存）在
    DTO 中显式表达；Claim 状态改变必须经过正式 use case/gate。
    M13-R1：claim 视图只包含 relation 命中本 run evidence 的 claim
    （跨 run 泄漏修复）；无 relation 的 claim 不归属任何 run。
    畸形 ledger 行（evidence_relations 非 JSON）不再 422 崩溃：
    整图降级标记 degraded=true（WP-P4）。
    """
    deps: ApiDeps = get_deps(request)
    ledger = _ledger_of(deps)
    try:
        claims, unsupported, contradictions = _claim_map_for_run(ledger, run_id)
    except Exception:  # noqa: BLE001 - ledger 行损坏时降级而非整体 422
        return ClaimMapDto(
            claims=[],
            unsupported_claims=[],
            contradictory_claims=[],
            degraded=True,
        )
    return ClaimMapDto(
        claims=claims,
        unsupported_claims=unsupported,
        contradictory_claims=contradictions,
        degraded=False,
    )


@router.get("/runs/{run_id}/usage", response_model=BudgetViewDto)
async def run_usage(run_id: str, request: Request) -> BudgetViewDto:
    """Budget/Usage 视图：正式 UsageLedger truth。

    - UNKNOWN 成本显式标记（禁止显示 0）；
    - estimated/actual 区分（KNOWN 时 estimated_cost_minor 必有）；
    - reservations 来自正式 ledger snapshot。
    """
    deps: ApiDeps = get_deps(request)
    if deps.budget is None:
        raise ApiError(503, "Budget Ledger Unavailable", "budget ledger not configured")
    snapshot = deps.budget.snapshot()
    entries = [
        UsageEntryDto(
            entry_id=entry.entry_id,
            resource_type=entry.resource_type.value,
            quantity=entry.quantity,
            unit=entry.unit,
            cost_status=entry.cost_status.value,
            estimated_cost_minor=entry.estimated_cost_minor,
            actual_cost_minor=entry.actual_cost_minor,
            model_id=entry.model_id,
            task_id=entry.task_id,
        )
        for entry in snapshot.entries
    ]
    known = sum(entry.estimated_cost_minor or 0 for entry in snapshot.entries)
    unknown_count = sum(
        1 for entry in snapshot.entries if entry.cost_status is LedgerCostStatus.UNKNOWN
    )
    return BudgetViewDto(
        entries=entries,
        total_estimated_cost_minor=known,
        unknown_cost_entries=unknown_count,
        reservations=[
            {
                "id": item.id,
                "scope": item.scope,
                "resource_type": item.resource_type.value,
                "quantity": item.quantity,
                "unit": item.unit,
            }
            for item in snapshot.reservations
        ],
    )


@router.get("/runs/{run_id}/export", response_model=ExportBundleDto)
async def run_export(run_id: str, request: Request) -> ExportBundleDto:
    """Audit/Export：来自 persisted state（canonical 重算），不导出 UI 内存。"""
    deps: ApiDeps = get_deps(request)
    run = get_run_or_error(deps, run_id)
    ledger = _ledger_of(deps)
    usage = await run_usage(run_id, request)
    claims = await run_claim_map(run_id, request)
    return ExportBundleDto(
        run_id=run_id,
        run_state=run.state,
        manifest_digest=str(run.manifest_digest) if run.manifest_digest else None,
        evidence=[_evidence_dto(item) for item in _evidence_of_run(ledger, run_id)],
        claims=claims.claims,
        usage=usage,
        exported_from="persisted-state",
    )
