"""Run 收敛守卫：resume 冻结语义校验与预算预留释放。

单一职责：把"run 收敛时必须执行的防线"集中为纯函数，
供 RunOrchestrationService 调用；不持有编排状态。
"""

from __future__ import annotations

from packages.application.ports.budget_ledger import BudgetLedger
from packages.application.ports.resource_catalog import PreflightContext
from packages.application.preflight.preflight import ManifestFreezeError, freeze_manifest
from packages.domain.core import Digest
from packages.domain.protocols import CompiledRunPlan, PreflightReport


def assert_semantics_frozen(
    run_id: str,
    semantic_digest: Digest | None,
    plan: CompiledRunPlan,
    report: PreflightReport,
    preflight: PreflightContext,
) -> None:
    """resume 前强制冻结语义校验：plan/catalog/契约漂移一律拒绝。

    语义 digest 缺失（旧快照）同样拒绝——不能静默放行未校验的恢复。
    """
    if semantic_digest is None:
        raise ManifestFreezeError(
            "frozen manifest lacks a semantic digest; fork run or revision required"
        )
    if not report.passed:
        raise ManifestFreezeError("cannot resume from a non-passing preflight report")
    reconstructed = freeze_manifest(run_id, plan, report, preflight)
    if reconstructed.semantic_digest() != semantic_digest:
        raise ManifestFreezeError(
            "resume semantics drifted from frozen manifest; fork run or revision required"
        )


def release_reservation(
    refs: dict[str, str], budget: BudgetLedger | None, run_id: str
) -> None:
    """run 收敛（成功/失败/取消）后幂等释放预算预留（BUDGET_QUOTA.md §2）。"""
    ref = refs.pop(run_id, None)
    if ref is not None and budget is not None:
        budget.release(ref)