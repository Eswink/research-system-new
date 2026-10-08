"""验收门求值结论的落库（GOAL-20261008-035 EC-01）。

`GateOutcome.evaluations` 一直携带「哪一条判据 / 过没过 / 判词里的数是多少」，但此前
**只有被拒的路径**把它带进失败消息（`gate_rejection_reason`）；通过的路径上这份结论
哪里都读不到（`ReviewFinding` / `Decision` 都是纯内存对象，从不持久化）⇒「覆盖判据在
这一次 run 里真的判过、两个维度各自的数是多少」不可复核。本模块把求值结论落到
canonical 存储，**两种结局都记**（对称 —— 被拒时的读法与通过时一致，反证判据因此能读
同一张面）。

**记录，不是重算**：读面必须能区分「门判过」与「门根本没跑」。派生式读面（读取时按
canonical 事实重跑一遍判据）在一扇从未求值的门上照样会给出结论 —— 那是掩盖，不是留痕。

判词渲染**只有一处**（`criterion_line`）：落库的逐条判词与失败消息用的是同一个渲染，
不会出现「读面一套、失败消息另一套」。
"""

from __future__ import annotations

from typing import Any

from packages.application.ports.review_finding_store import ScopedReviewFinding
from packages.domain.evidence import ReviewFinding


def criterion_line(evaluation: Any) -> str:
    """一条判据的渲染（`判据名: 逐字判词`）——**唯一的渲染点**（读面与失败消息共用）。"""
    return f"{evaluation.criterion_type.value}: {evaluation.reason}"


def acceptance_finding(
    run_id: str, task_id: str, contract_id: str, gate: Any
) -> ScopedReviewFinding:
    """把门的求值结论包上作用域落库（**全量逐条**：判过与判负都在）。

    判词逐字来自域函数（`evaluation.reason`），只加判据名前缀 —— 不加前缀读者无法从
    读面知道「这句话是哪条判据说的」，而失败路径早已是这个约定。
    """
    return ScopedReviewFinding(
        finding=ReviewFinding(
            id=gate.review_finding.id,
            review_type=gate.review_finding.review_type,
            verdict=gate.verdict,
            findings=[criterion_line(item) for item in gate.evaluations],
            reviewed_by=gate.review_finding.reviewed_by,
            reviewed_at=gate.review_finding.reviewed_at,
        ),
        run_id=run_id,
        task_id=task_id,
        contract_id=contract_id,
    )


def record_acceptance_evaluation(deps: Any, tctx: Any, gate: Any) -> None:
    """把这一次门的求值结论落库（**通过与被拒都记**）。

    未接存储（`deps.review_findings is None`）⇒ 不记：这是**装配面**的缺省，不是
    「判过」的替身 —— 生产组合根总是接上，判据面（`tests/e2e`）断言默认装配上有这条结论。
    """
    store = getattr(deps, "review_findings", None)
    if store is None:
        return
    store.put(
        acceptance_finding(
            tctx.ctx.run_id,
            tctx.task.id.value,
            tctx.contract.id,
            gate,
        )
    )


__all__ = ["acceptance_finding", "criterion_line", "record_acceptance_evaluation"]
