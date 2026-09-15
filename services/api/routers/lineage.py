"""来源血缘只读路由（run 级 PLAN-043 WP-A；项目级 G9 / GOAL-20260915-002 EC-01）。

- `GET /runs/{run_id}/lineage`：run 级投影（evidence/claim 引用）。
- `GET /projects/{project_id}/lineage`：项目级合并图（同一套投影规则作用到项目每个 run，
  按节点 id 合并 ⇒ 跨 run 关系由**共享节点**表达）；库资源以未连边清单呈现，
  `reference_recording` 如实说明"资源引用无记录面"。

投影规则单一来源：`services/api/lineage_projection.py`。路由只做装配与错误面。
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from packages.application.ports import EvidenceLedger
from packages.domain.library import LibraryResource, ResourceKind
from packages.domain.run import ResearchRun
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.inspection import LineageDto, ProjectLineageDto
from services.api.errors import ApiError
from services.api.lineage_projection import run_lineage_nodes_edges
from services.api.project_lineage import project_lineage
from services.api.run_access import get_run_or_error

router = APIRouter(tags=["inspection"])

GLOBAL_LINEAGE_REASON = "全局数据集/提示词血缘无 API（G9）：仅 Run 级引用"


def _ledger_of(deps: ApiDeps) -> EvidenceLedger:
    if deps.ledger is None:
        raise ApiError(503, "Evidence Ledger Unavailable", "evidence ledger not configured")
    return deps.ledger


def _project_runs(deps: ApiDeps, project_id: str) -> list[ResearchRun]:
    """项目 runs 的单一读取路径（runs store 优先，registry 兜底，与 runs 路由同口径）。"""
    if deps.runs_store is not None:
        return list(deps.runs_store.list_runs(project_id))
    return [run for run in (deps.run_registry or {}).values() if run.project_id == project_id]


def _library_resources(deps: ApiDeps, project_id: str) -> list[LibraryResource]:
    """项目库资源（数据集/提示词/笔记本）；未配置 library store 时为空清单。"""
    store = deps.library_store
    if store is None:
        return []
    resources: list[LibraryResource] = []
    for kind in (ResourceKind.DATASET, ResourceKind.PROMPT, ResourceKind.NOTEBOOK):
        resources.extend(store.list_resources(project_id, kind))
    return resources


@router.get("/runs/{run_id}/lineage", response_model=LineageDto)
async def run_lineage(run_id: str, request: Request) -> LineageDto:
    """Run 级来源血缘（nodes/edges 由 persisted evidence/claim 投影）。

    未知 run → 404；ledger 损坏 → degraded=true（不整体 422）；项目级血缘见
    `GET /projects/{project_id}/lineage`。
    """
    deps: ApiDeps = get_deps(request)
    ledger = _ledger_of(deps)
    get_run_or_error(deps, run_id)
    try:
        nodes, edges = run_lineage_nodes_edges(ledger, run_id)
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
        global_lineage_reason=GLOBAL_LINEAGE_REASON,
    )


@router.get("/projects/{project_id}/lineage", response_model=ProjectLineageDto)
async def project_lineage_view(project_id: str, request: Request) -> ProjectLineageDto:
    """项目级来源血缘（项目 runs 的合并图 + 库资源未连边清单）。

    未知项目 → 空图（与 `/projects/{id}/runs`、`/projects/{id}/experiments` 同口径，
    不 404）；ledger 未配置 → 503；单 run 行损坏 → 整图 degraded=true 并给出原因。
    """
    deps: ApiDeps = get_deps(request)
    ledger = _ledger_of(deps)
    return project_lineage(
        project_id=project_id,
        runs=_project_runs(deps, project_id),
        ledger=ledger,
        library_resources=_library_resources(deps, project_id),
    )


__all__ = ["GLOBAL_LINEAGE_REASON", "router"]
