"""`research_state.read` 的**执行实现**（GOAL-20261008-037 EC-03）。

**它读什么**：**本 run 所属程序内、前序 run 的落库结论**。入口是 `run_id`（执行期注入，
`run_id_argument=True`）—— 由它反查本 run 的 `program_id`（`RunStore.get_run`），再用
`RunStore.for_program` 取出该程序的全部 run，**排除本 run 自己**，最后把每个前序 run 的
终态与**逐字评审结论**（`ReviewFindingStore.for_run`）汇成一份读面载荷。

**为什么这是「跨 run 知识累积」而不是「再读一遍本 run」**：`run.read` / `review.read` 读的是
**本 run**；本工具读的是**别的 run**（同一程序内的前序轮次），这正是 GOAL-037 要补的那一环
（前序 run 的结论此前对后续 run 完全不可见）。

**它**不**读什么**（边界写进实现，防止被读成「万能研究状态面」）：

- **不**读 memory（决策 ④：memory 的项目维度是另一条线）；
- **不**读证据链正文（那是 `evidence.read` / `claim.read` 的职责）；
- **不**跨程序（入口是本 run 的**程序归属**；本 run 不属于任何程序 ⇒ **点名**，不猜）。

**缺依赖 / 缺归属点名**（与既有读面同一条纪律）：`RunStore` / `ReviewFindingStore` 缺失、
run 未知、或本 run 不属于任何程序 ⇒ **点名拒绝**，**不**返回空壳冒充「没有前序知识」。
"""

from __future__ import annotations

from typing import Any

from packages.application.ports.errors import InvalidInputError


def _conclusion_row(findings: Any | None, run_id: str) -> dict[str, object]:
    """一个前序 run 的评审结论（逐条判词**去重保序**；读不到 ⇒ 空数组，不编造）。"""
    if findings is None:
        return {"verdicts": [], "reviewed_by": None}
    verdicts: list[str] = []
    reviewed_by: str | None = None
    for record in findings.for_run(run_id):
        verdict = str(record.finding.verdict)
        if verdict not in verdicts:
            verdicts.append(verdict)
        reviewed_by = record.finding.reviewed_by or reviewed_by
    return {"verdicts": verdicts, "reviewed_by": reviewed_by}


def research_state_read(
    runs: Any | None,
    findings: Any | None,
    args: dict[str, object],
) -> dict[str, object]:
    """读**本 run 所属程序内前序 run** 的落库结论（入口 = run_id → 程序归属）。

    载荷形状（读面契约）：

    - `run_id`：入口（本 run）；
    - `program_id`：本 run 的程序归属（由 run 反查；不是外部传入的猜测）；
    - `prior_run_count`：前序轮次数（**构造性为零**表示本 run 是程序的第一轮）；
    - `prior_runs`：前序 run 逐条（`run_id` / `program_index` / `state` /
      `manifest_digest` / `verdicts`（**逐字判词**）/ `reviewed_by`）。
    """
    if runs is None:
        raise InvalidInputError(
            "research_state_read requires a RunStore, which is not in this assembly"
        )
    run_id = str(args.get("run_id") or "").strip()
    if not run_id:
        raise InvalidInputError("research_state_read requires a non-empty run_id")
    run = runs.get_run(run_id)
    program_id = run.program_id
    if not program_id:
        raise InvalidInputError(
            f"run {run_id} belongs to no research program "
            "(the program is the read entry for prior-run knowledge; not guessed)"
        )
    prior = [item for item in runs.for_program(program_id) if item.id.value != run_id]
    rows: list[dict[str, object]] = []
    for item in prior:
        rows.append({
            "run_id": item.id.value,
            "program_index": item.program_index,
            "state": str(item.state),
            "manifest_digest": str(item.manifest_digest) if item.manifest_digest else None,
            **_conclusion_row(findings, item.id.value),
        })
    return {
        "run_id": run_id,
        "program_id": program_id,
        "prior_run_count": len(rows),
        "prior_runs": rows,
    }


__all__ = ["research_state_read"]
