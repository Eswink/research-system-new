"""Run 收敛守卫：resume 冻结语义校验与预算预留释放。

单一职责：把"run 收敛时必须执行的防线"集中为纯函数，
供 RunOrchestrationService 调用；不持有编排状态。
"""

from __future__ import annotations

from dataclasses import replace

from packages.application.ports.budget_ledger import BudgetLedger
from packages.application.preflight.preflight import ManifestFreezeError, freeze_manifest
from packages.application.run_orchestration.context import RunContext


def assert_semantics_frozen(
    context: RunContext,
    *,
    pricing_version: str | None = None,
    pricing_digest: str | None = None,
) -> None:
    """resume 前强制冻结语义校验：plan/catalog/契约漂移一律拒绝。

    语义 digest 缺失（旧快照）同样拒绝——不能静默放行未校验的恢复。
    重建 manifest 时必须回填 run 冻结的定价引用：定价引用随 manifest 一起
    参与 semantic digest，重建若不回填就会把"价表版本推进"误判为语义漂移
    （resume 语义应保持原 run 冻结的引用，而不是用读时当期表重盖章）。
    """
    if context.run.manifest_semantic_digest is None:
        raise ManifestFreezeError(
            "frozen manifest lacks a semantic digest; fork run or revision required"
        )
    if not context.report.passed:
        raise ManifestFreezeError("cannot resume from a non-passing preflight report")
    reconstructed = freeze_manifest(
        context.run.id.value, context.plan, context.report, context.preflight
    )
    if pricing_version is not None or pricing_digest is not None:
        reconstructed = replace(
            reconstructed,
            pricing_version=pricing_version,
            pricing_digest=pricing_digest,
        )
    if reconstructed.semantic_digest() != context.run.manifest_semantic_digest:
        raise ManifestFreezeError(
            "resume semantics drifted from frozen manifest; fork run or revision required"
        )


def release_reservation(refs: dict[str, str], budget: BudgetLedger | None, run_id: str) -> None:
    """run 收敛（成功/失败/取消）后幂等释放预算预留（BUDGET_QUOTA.md §2）。"""
    ref = refs.pop(run_id, None)
    if ref is not None and budget is not None:
        budget.release(ref)
