"""来源血缘投影（run 级规则单一来源）。

`GET /runs/{run_id}/lineage`（run 级）与 `GET /projects/{id}/lineage`（项目级，
G9）必须用**同一套**投影规则：节点/边的定义只在这里维护，路由只做装配与错误面。
项目级也只是"把同一规则作用到项目的每个 run 再合并"——不引入第二套语义。

只由 API 明确返回的引用构造边：source_ref→evidence、evidence→claim、
evidence→artifact、evidence→model。缺失引用不补节点（断开而非编造）。
"""

from __future__ import annotations

from collections.abc import Callable

from packages.application.ports import EvidenceLedger
from packages.domain.evidence import Evidence
from services.api.dto.inspection import LineageEdgeDto, LineageNodeDto

_AddNode = Callable[[str, str, str], None]


def run_lineage_nodes_edges(
    ledger: EvidenceLedger, run_id: str
) -> tuple[list[LineageNodeDto], list[LineageEdgeDto]]:
    """由 evidence/claim 投影 run 级 typed 节点与边（确定性排序）。"""
    nodes: dict[str, LineageNodeDto] = {}
    edges: list[LineageEdgeDto] = []

    def add_node(node_id: str, kind: str, label: str) -> None:
        nodes.setdefault(node_id, LineageNodeDto(id=node_id, kind=kind, label=label, run_id=run_id))

    evidence_items = _evidence_of_run(ledger, run_id)
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


def _evidence_of_run(ledger: EvidenceLedger, run_id: str) -> tuple[Evidence, ...]:
    """run 的 evidence 集合：经 claim→relation→evidence 遍历（ledger 无全表列举）。

    与 `services/api/run_evidence.py::evidence_of_run` 同规则；此处内联是为了让
    投影模块自洽（避免路由层与投影层互相 import）。
    """
    seen: dict[str, Evidence] = {}
    for claim in ledger.claims():
        for relation in ledger.relations_for_claim(claim.id):
            try:
                evidence = ledger.get_evidence(relation.evidence_id)
            except Exception:  # noqa: BLE001 - 引用已删除：跳过该边，不整体失败
                continue
            if evidence.run_id == run_id:
                seen.setdefault(evidence.id, evidence)
    return tuple(seen[key] for key in sorted(seen))


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


__all__ = ["run_lineage_nodes_edges"]
