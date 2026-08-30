"""M15 run 级定价解析：按冻结引用寻址历史价表（BLOCKER-6 解析侧）。

历史投影按 run 冻结的 (pricing_version, pricing_digest) 从快照存储寻址，
而不是读时传入的当期表——价格后续变更产生新版本,已冻结 run 的历史投影
不可被改写。解析失败显式降级,绝不回落当期表。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.cost.pricing import PricingTable
from packages.application.ports.pricing_snapshot_store import PricingSnapshotStore
from packages.domain.run import ResearchRun

UNFROZEN_PRICING_VERSION = "unfrozen"


@dataclass(frozen=True, slots=True)
class RunPricingResolution:
    """run 级定价解析结果(BLOCKER-6:历史投影按冻结引用寻址)。

    三态:
    - frozen=True 且 degraded_reason=None:快照命中,`pricing` 是冻结时的
      历史价表,投影按它计价盖章;
    - frozen=True 且 degraded_reason 非 None:冻结引用存在但快照存储缺失
      或未接线——存储完整性事故,计算型金额全部 MONETARY_UNAVAILABLE,
      **绝不回落当期表**(那正是本 BLOCKER 的成因);
    - frozen=False:遗留 run(冻结先于定价冻结机制),显式表达
      "pricing 未冻结",同样不回落当期表。

    `pricing_version` / `pricing_digest` 是视图级盖章:快照命中时为表自身
    的版本/摘要,否则为冻结引用原文(或 "unfrozen")。
    """

    pricing: PricingTable | None
    pricing_version: str
    pricing_digest: str
    frozen: bool
    degraded_reason: str | None


def resolve_run_pricing(
    run: ResearchRun | None,
    store: PricingSnapshotStore | None,
    current: PricingTable | None = None,
) -> RunPricingResolution:
    """按 run 冻结的 pricing 引用从快照存储解析历史价表。

    `current`(读时当期表)只用作 NO_DATA 等空结果的盖章上下文,永远不参与
    计价——传不传它都不改变"冻结引用优先、不可解析即显式降级"的结论。
    """
    del current  # 只读上下文,永不参与计价(见 BLOCKER-6)
    version = run.pricing_version if run is not None else None
    digest = run.pricing_digest if run is not None else None
    if not (version and digest):
        # 遗留 run:显式 "pricing 未冻结",不回落当期表。
        return RunPricingResolution(
            pricing=None,
            pricing_version=UNFROZEN_PRICING_VERSION,
            pricing_digest="",
            frozen=False,
            degraded_reason="pricing not frozen for this run",
        )
    if store is None:
        return _missing_store(version, digest)
    table = store.get(version, digest)
    if table is not None:
        return RunPricingResolution(
            pricing=table,
            pricing_version=table.version,
            pricing_digest=table.pricing_digest(),
            frozen=True,
            degraded_reason=None,
        )
    return _missing_snapshot(version, digest)


def _missing_store(version: str, digest: str) -> RunPricingResolution:
    return RunPricingResolution(
        pricing=None,
        pricing_version=version,
        pricing_digest=digest,
        frozen=True,
        degraded_reason=(
            "run froze a pricing reference but no pricing snapshot store is configured;"
            " computed amounts are unavailable (no current-table fallback)"
        ),
    )


def _missing_snapshot(version: str, digest: str) -> RunPricingResolution:
    return RunPricingResolution(
        pricing=None,
        pricing_version=version,
        pricing_digest=digest,
        frozen=True,
        degraded_reason=(
            f"frozen pricing snapshot {version}@{digest[:12]} missing from store;"
            " computed amounts are unavailable (no current-table fallback)"
        ),
    )


__all__ = [
    "RunPricingResolution",
    "UNFROZEN_PRICING_VERSION",
    "resolve_run_pricing",
]
