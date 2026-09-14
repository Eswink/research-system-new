"""Run 级来源血缘只读路由（PLAN-043 WP-A，EC-02）。

`GET /runs/{run_id}/lineage` 由 persisted evidence/claim 投影 typed nodes/edges
（确定性排序）。边只来自 API 明确返回的引用；全局跨 run 血缘无 API（G9），
恒标注不可用，不猜测连边。
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Request

from packages.application.ports import EvidenceLedger
from packages.domain.evidence import Evidence
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.inspection import LineageDto, LineageEdgeDto, LineageNodeDto
from services.api.errors import ApiError
from services.api.run_access import get_run_or_error
from services.api.run_evidence import evidence_of_run

router = APIRouter(tags=["inspection"])

_GLOBAL_LINEAGE_REASON = "全局数据集/提示词血缘无 API（G9）：仅 Run 级引用"
_AddNode = Callable[[str, str, str], None]


def _ledger_of(deps: ApiDeps) -> EvidenceLedger:
    if deps.ledger is None:
        raise ApiError(503, "Evidence Ledger Unavailable", "evidence ledger not configured")
    return deps.ledger


def _lineage_nodes_edges(
    ledger: EvidenceLedger, run_id: str
) -> tuple[list[LineageNodeDto], list[LineageEdgeDto]]:
    """由 evidence/claim 投影 run 级 typed 节点与边（确定性排序）。

    边只来自 API 明确返回的引用：source_ref→evidence、evidence→claim、
    evidence→artifact、evidence→model。缺失引用不补节点（断开而非编造）。
    """
    nodes: dict[str, LineageNodeDto] = {}
    edges: list[LineageEdgeDto] = []

    def add_node(node_id: str, kind: str, label: str) -> None:
        nodes.setdefault(node_id, LineageNodeDto(id=node_id, kind=kind, label=label, run_id=run_id))

    evidence_items = evidence_of_run(ledger, run_id)
    evidence_ids = {item.id for item in evidence_items}
    for evidence in evidence_items:
        evidence_node = f"evidence:{evidence.id}"
        add_node(evidence_node, "evidence", evidence.source_ref)
        source_node = f"source:{evidence.source_ref}"
        add_node(source_node, "source", evidence.source_ref)
        edges.append(LineageEdgeDto(source=source_node, target=evidence_node, relation="cited_by"))
        edges.extend(_artifact_edges(evidence, evidence_node, add_node))
        edges.extend(_model_edges(evidence, evidence_node, add_node))

    for claim in ledger.claims():
        scoped = tuple(
            relation
            for relation in ledger.relations_for_claim(claim.id)
            if relation.evidence_id in evidence_ids
        )
        if not scoped:
            continue
        claim_node = f"claim:{claim.id}"
        add_node(claim_node, "claim", claim.statement)
        for relation in scoped:
            edges.append(
                LineageEdgeDto(
                    source=f"evidence:{relation.evidence_id}",
                    target=claim_node,
                    relation=relation.relation.value.lower(),
                )
            )

    ordered_nodes = sorted(nodes.values(), key=lambda item: (item.kind, item.id))
    ordered_edges = sorted(edges, key=lambda item: (item.source, item.target, item.relation))
    return ordered_nodes, ordered_edges


def _artifact_edges(
    evidence: Evidence,
    evidence_node: str,
    add_node: _AddNode,
) -> list[LineageEdgeDto]:
    artifact_id = evidence.artifact_id
    if not artifact_id:
        return []
    artifact_node = f"artifact:{artifact_id}"
    add_node(artifact_node, "artifact", artifact_id)
    return [LineageEdgeDto(source=evidence_node, target=artifact_node, relation="materialized_as")]


def _model_edges(
    evidence: Evidence,
    evidence_node: str,
    add_node: _AddNode,
) -> list[LineageEdgeDto]:
    edges: list[LineageEdgeDto] = []
    for model_ref in evidence.model_refs:
        model_node = f"model:{model_ref}"
        add_node(model_node, "model", model_ref)
        edges.append(
            LineageEdgeDto(source=evidence_node, target=model_node, relation="produced_with")
        )
    return edges


@router.get("/runs/{run_id}/lineage", response_model=LineageDto)
async def run_lineage(run_id: str, request: Request) -> LineageDto:
    """Run 级来源血缘（nodes/edges 由 persisted evidence/claim 投影）。

    未知 run → 404；ledger 损坏 → degraded=true（不整体 422）；全局跨 run
    血缘恒不可用（无 API，G9 诚实锁定，不猜测连边）。
    """
    deps: ApiDeps = get_deps(request)
    ledger = _ledger_of(deps)
    get_run_or_error(deps, run_id)
    try:
        nodes, edges = _lineage_nodes_edges(ledger, run_id)
    except Exception:  # noqa: BLE001 - ledger 行损坏时降级而非整体 422
        return LineageDto(
            run_id=run_id,
            nodes=[],
            edges=[],
            global_lineage_available=False,
            global_lineage_reason="ledger 行损坏，血缘图降级",
            degraded=True,
        )
    return LineageDto(
        run_id=run_id,
        nodes=nodes,
        edges=edges,
        global_lineage_available=False,
        global_lineage_reason=_GLOBAL_LINEAGE_REASON,
    )
