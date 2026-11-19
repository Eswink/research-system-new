"""Panel advice：**只读**的「评审小组建议」读数（GOAL-20261119-115 EC-05）。

**它是第二读面，不是第二个真相**：硬门（`acceptance_criteria` 的
`REVIEW_SCORE ≥ 0.8` + `review_panel_judging.panel_rejection()`）**一字不改**。
本模块只把 `evaluation.panel_verdict.aggregate_panel` 已算出的聚合结果按
**被评对象**（`phase_id`）分组读出来，让「1 负 1 过」这种分歧在**不改变 run 终态**的
前提下可读。

**三条边界（判据盯着它们）**：

1. **不产生 `Decision`**：本模块不 import `Decision`，也不返回任何能当验收结论用的东西；
2. **不调 `deps.fail`**：它拿不到 deps，签名里就没有；
3. **不改 `panel_rejection`**：那个函数本文件不认识。

**分组键是 `phase_id`，不是 `task_id`**：同一 phase 上每个评审 agent 各拿一个
`ResearchTask`，所以 `task_id` 标识的是**谁在评**而不是**评的是哪一批**。按 `task_id`
分组时每组至多一条判词 ⇒ 评审小组**永远不存在**（`ScopedReviewFinding` 的文档逐字
警告过这一点）。`phase_id is None` 的记录**不并进任何组**，并逐条点名 ——
既不并组也不丢弃。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from packages.application.evaluation.panel_verdict import aggregate_panel
from packages.application.ports.review_finding_store import ScopedReviewFinding


@dataclass(frozen=True, slots=True)
class PanelAdvice:
    """一个**被评对象**（phase）上的建议性读数。

    `verdict is None` 有三种成因，且**必须彼此可读**（不合并成一句"无结论"）：
    该组只有一份判词（单评审不聚合）、或没有可归因的票、或全部无法投票。
    成因写进 `notes`，`voters` / `ineligible` 各自可数。
    """

    phase_id: str
    voters: int = 0
    votes: dict[str, int] = field(default_factory=dict)
    advisory: str | None = None
    dissent: tuple[str, ...] = ()
    ineligible: tuple[str, ...] = ()
    targets: tuple[str, ...] = ()
    independent: bool = False
    independence_notes: tuple[str, ...] = ()
    #: 为什么这一组没有聚合结论（`None` 表示有结论）。**空不是缺陷，含糊才是**。
    notes: tuple[str, ...] = ()

    @property
    def decided(self) -> bool:
        """有明确多数结论（不是平票、不是无票）。"""
        return self.advisory is not None

    def as_payload(self) -> dict[str, Any]:
        return {
            "phase_id": self.phase_id,
            "voters": self.voters,
            "votes": dict(self.votes),
            "advisory": self.advisory,
            "dissent": list(self.dissent),
            "ineligible": list(self.ineligible),
            "targets": list(self.targets),
            "independent": self.independent,
            "independence_notes": list(self.independence_notes),
            "notes": list(self.notes),
        }


def panel_advice(findings: tuple[ScopedReviewFinding, ...]) -> tuple[PanelAdvice, ...]:
    """按 `phase_id` 分组，把每组聚合成一条**建议性**读数（按 `phase_id` 排序）。

    `phase_id is None` 的记录不进任何组：它们没有「评的是哪一批」这一格，
    并进去会把两个不同批次的判词混成一次投票（那是**伪造**小组，比"读不到"更坏）。
    """
    grouped, ungrouped = _group_by_phase(findings)
    advice = [_advice_for(phase_id, items) for phase_id, items in sorted(grouped.items())]
    if ungrouped:
        advice.append(
            PanelAdvice(
                phase_id="<unattributed>",
                notes=(
                    f"{len(ungrouped)} finding(s) carry no phase_id and were not aggregated: "
                    f"{', '.join(ungrouped)}",
                ),
            )
        )
    return tuple(advice)


def _group_by_phase(
    findings: tuple[ScopedReviewFinding, ...],
) -> tuple[dict[str, list[ScopedReviewFinding]], list[str]]:
    """分组 + 点名无归属记录（`phase_id is None` 的那些 finding id）。

    **单一归属、不重复计入**：一条记录只会落进一个组或 `ungrouped`，
    不会既进组又出现在点名里（否则读面会把同一份判词数两次）。
    """
    grouped: dict[str, list[ScopedReviewFinding]] = {}
    ungrouped: list[str] = []
    for item in findings:
        if item.phase_id is None:
            ungrouped.append(item.finding.id)
            continue
        grouped.setdefault(item.phase_id, []).append(item)
    return grouped, ungrouped


def _advice_for(phase_id: str, items: list[ScopedReviewFinding]) -> PanelAdvice:
    """一组的读数：`aggregate_panel` 有结论就用它，没有就点名**为什么**没有。"""
    verdict = aggregate_panel([item.finding for item in items])
    if verdict is None:
        return PanelAdvice(
            phase_id=phase_id,
            voters=0,
            notes=(
                f"only {len(items)} finding(s) on this phase; a panel needs at least two "
                "(a single review is not aggregated)",
            ),
        )
    return PanelAdvice(
        phase_id=phase_id,
        voters=verdict.voters,
        votes=dict(verdict.votes),
        advisory=verdict.advisory,
        dissent=tuple(verdict.dissent),
        ineligible=tuple(verdict.ineligible),
        targets=tuple(verdict.targets),
        independent=verdict.independent,
        independence_notes=tuple(verdict.independence_notes),
        notes=() if verdict.decided else ("no majority: the votes tie or nobody could vote",),
    )


__all__ = ["PanelAdvice", "panel_advice"]
