"""项目级来源血缘装配（G9 / GOAL-20260915-002 EC-01）。

投影规则见 `services/api/lineage_projection.py`（与 run 级同源）。本模块只负责：
取项目 runs → 逐个投影 → **按节点 id 合并**（同一 id 由多个 run 贡献即"跨 run 共享"）
→ 附上项目库资源的未连边清单与诚实的记录面说明。

诚实边界（随响应一起返回，不得只在文档里说）：

- 数据集/提示词与 run 的引用关系**当前没有任何记录面**：协议定义只有
  `id/version/phases`，`RunManifest` 只有 `evaluation_dataset_digest`（摘要无法反查
  `LibraryResource`），evidence 的 `source_ref` 也不携带资源 id。因此库资源只作为
  **未连边清单**呈现（`reference_recording=NOT_RECORDED`），不画任何 run↔dataset/prompt 边。
- 不跨项目合并：节点只来自该项目 runs 的 evidence/claim 与该项目库资源。
- ledger 行损坏 → 该 run 的投影失败不应打垮整个图：整图降级标记 + 原因。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from packages.application.ports import EvidenceLedger
from packages.domain.library import LibraryResource
from packages.domain.run import ResearchRun
from services.api.dto.inspection import (
    LineageEdgeDto,
    ProjectLineageDto,
    ProjectLineageNodeDto,
    ProjectLineageResourceDto,
)
from services.api.lineage_projection import run_lineage_nodes_edges

REFERENCE_RECORDING_NOT_RECORDED = "NOT_RECORDED"
_REFERENCE_REASON = (
    "run 与数据集/提示词的引用关系无记录面（协议定义与 RunManifest 均不含资源 id），"
    "库资源以未连边清单呈现，不猜测连边"
)
_DEGRADED_REASON = "ledger 行损坏：部分 run 的血缘投影失败，已降级"


@dataclass(slots=True)
class _MergedNode:
    """合并中的节点：同一 id 可能由多个 run 贡献。"""

    id: str
    kind: str
    label: str
    run_ids: list[str] = field(default_factory=list)


def project_lineage(
    *,
    project_id: str,
    runs: list[ResearchRun],
    ledger: EvidenceLedger,
    library_resources: list[LibraryResource],
) -> ProjectLineageDto:
    """把项目内每个 run 的血缘投影合并成一张图（确定性排序）。"""
    nodes, edges, degraded = _merge_runs(runs, ledger)
    return ProjectLineageDto(
        project_id=project_id,
        run_count=len(runs),
        nodes=_node_dtos(nodes),
        edges=[edges[key] for key in sorted(edges)],
        library_resources=_resource_dtos(library_resources),
        reference_recording=REFERENCE_RECORDING_NOT_RECORDED,
        reference_recording_reason=_REFERENCE_REASON,
        degraded=degraded,
        degraded_reason=_DEGRADED_REASON if degraded else None,
    )


def _merge_runs(
    runs: list[ResearchRun],
    ledger: EvidenceLedger,
) -> tuple[dict[str, _MergedNode], dict[tuple[str, str, str], LineageEdgeDto], bool]:
    """逐 run 投影并按节点 id 合并；单 run 行损坏只置降级标记。"""
    nodes: dict[str, _MergedNode] = {}
    edges: dict[tuple[str, str, str], LineageEdgeDto] = {}
    degraded = False
    for run in sorted(runs, key=lambda item: item.id.value):
        run_id = run.id.value
        _merge(nodes, f"run:{run_id}", "run", run_id, run_id)
        try:
            run_nodes, run_edges = run_lineage_nodes_edges(ledger, run_id)
        except Exception:  # noqa: BLE001 - 单 run 行损坏降级，不整体失败
            degraded = True
            continue
        for node in run_nodes:
            _merge(nodes, node.id, node.kind, node.label, run_id)
        for edge in run_edges:
            edges[(edge.source, edge.target, edge.relation)] = edge
    return nodes, edges, degraded


def _node_dtos(nodes: dict[str, _MergedNode]) -> list[ProjectLineageNodeDto]:
    return [
        ProjectLineageNodeDto(
            id=node.id,
            kind=node.kind,
            label=node.label,
            run_ids=sorted(node.run_ids),
            shared=len(node.run_ids) > 1,
        )
        for node in sorted(nodes.values(), key=lambda item: (item.kind, item.id))
    ]


def _resource_dtos(resources: list[LibraryResource]) -> list[ProjectLineageResourceDto]:
    return [
        ProjectLineageResourceDto(
            id=resource.id,
            kind=resource.kind.value,
            name=resource.name,
            status=resource.status.value,
        )
        for resource in sorted(resources, key=lambda item: item.id)
    ]


def _merge(nodes: dict[str, _MergedNode], node_id: str, kind: str, label: str, run_id: str) -> None:
    existing = nodes.get(node_id)
    if existing is None:
        nodes[node_id] = _MergedNode(id=node_id, kind=kind, label=label, run_ids=[run_id])
        return
    if run_id not in existing.run_ids:
        existing.run_ids.append(run_id)


__all__ = ["REFERENCE_RECORDING_NOT_RECORDED", "project_lineage"]
