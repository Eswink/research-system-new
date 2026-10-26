"""创新点声明的**编排接线**（GOAL-20261026-097 EC-04(a)：判定面真的进验收门）。

**为什么单列**：`task_phase_helpers.py` 已 449/450 行、`evaluate_gate` 43 行（函数门 50）
—— 判据本体在 `novelty_claim.py`（纯读取），接线（「哪一份契约要过这道门」+ 判词形态）
放这里，`evaluate_gate` 只多一次调用。

**判定与既有验收的关系（不改词表）**：本模块**不**新增 `AcceptanceCriterionType`，也不动
`evaluate_contract`。它在**既有门内**追加一条判据，并且**与既有判据并列**：
任一条不过 ⇒ 门不过；判词逐条进 `GateOutcome`（M9 的门面本来就支持多判据）。

**为什么判据必须落在这里而不是报告里**：报告是**汇编**（读已落库的事实），它没有
「拒绝」的权力 —— 一份站在不存在的前人工作上的创新声明会照样被汇编进报告。
门是唯一能在 run 内**判负**的位置。
"""

from __future__ import annotations

from typing import Any

#: 要求过创新点判据的合约 id（= `examples/contracts/task_contracts.yaml` 里那一份）。
NOVELTY_CONTRACT_ID = "novelty_claim_proposal"

#: 判据在门里的**名字**（判词前缀；读面按它归组，不靠顺序）。
NOVELTY_CRITERION = "NOVELTY_CLAIM_GROUNDED"


def novelty_verdict(deps: Any, tctx: Any) -> str | None:
    """本任务若声明了创新点（按**契约 id**），返回判词（`None` = 通过或不需要判）。

    三态明确分开（与 `novelty_claim` 同一纪律）：

    - **不需要判**（契约 id 不是 `novelty_claim_proposal`）⇒ `None`（既有行为逐字不变）；
    - **通过** ⇒ `None`（门自己会记录其余判据；本判据通过时不额外产出判词）；
    - **不通过** ⇒ 一句点名判词（带**真实**检索标识与被拒原因），由调用方并入门判词。

    「通过时不产出判词」是有意的：`GateOutcome.verdicts` 的既有语义是**逐条判据的结论**，
    在它之外凭空加一条「通过」会让既有读面的条数变（那是另一件事，不在本 GOAL）。
    """
    if str(tctx.contract.id) != NOVELTY_CONTRACT_ID:
        return None
    from packages.application.run_orchestration.novelty_claim import novelty_claim_of_run

    try:
        claim = novelty_claim_of_run(deps.artifacts, deps.ledger, str(tctx.task.run_id.value))
    except Exception as error:  # noqa: BLE001 - 判据自身失败必须**判负**，不静默放行
        return f"{NOVELTY_CRITERION} rejected: {error}"
    if claim is None:
        return (
            f"{NOVELTY_CRITERION} rejected: the task declared a novelty claim but no "
            "novelty_claim artifact is in this run's evidence (nothing to judge)"
        )
    return None


def with_novelty(deps: Any, tctx: Any, gate: Any) -> Any:
    """创新点判据并入门（不通过 ⇒ 门不过；其余合约逐字返回原 gate）。"""
    from dataclasses import replace

    rejection = novelty_verdict(deps, tctx)
    if rejection is None:
        return gate
    return replace(gate, passed=False, verdicts=(*gate.verdicts, rejection))


__all__ = [
    "NOVELTY_CONTRACT_ID",
    "NOVELTY_CRITERION",
    "novelty_verdict",
    "with_novelty",
]
