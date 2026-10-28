"""手稿的**事实读取面**（GOAL-20261028-099 EC-02/EC-03；自 `manuscript_task.py` 拆出守规模门）。

**为什么单列**：与 `report_facts.py` 从 `report_task.py` 拆出**同一手法** —— 「把持久事实
读成手稿输入」与「把字节准入 canonical」是两件事，判据与失败面都不同。

**读什么、从哪读**（本模块不新造第二套查询，也不重算任何数字）：

| 读什么 | 怎么读 | 与哪个既有读面同源 |
| --- | --- | --- |
| run / 协议 / 状态 / 问题 | `report_facts.report_inputs` | 报告汇编用的**同一个**函数 |
| 来源 / 指标 / 判词 | 同上（四个既有读面相） | `GET /runs/{id}/…` 各读面 |
| 文献元数据 | 同一条证据投影里的 tool-result 制品 `articles[]` | `references.reference_table` |

**复用 `report_inputs` 而不是另写一份**：手稿的数据表与报告的事实表**必须同源** ——
两处各读一遍，读者拿到的两个数迟早会漂。`ReportInputs` 是那份事实的**唯一**形状。

**如实边界**：本模块只认 `tool:` 前缀的工具证据（与 `count_retrieved_sources` 同一口径）；
声明输入（`USER_PROVIDED`）与自产件（`GENERATED`）都不是参考文献。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from packages.application.deliverable.references import ReferenceTable, reference_table
from packages.application.deliverable.research_report import ReportInputs
from packages.application.run_orchestration.report_facts import (
    evidence_of_run,
    report_inputs,
    tool_evidence,
)


@dataclass(frozen=True, slots=True)
class ManuscriptFacts:
    """手稿的全部正式输入（参数对象；避免函数参数超限）。"""

    inputs: ReportInputs
    references: ReferenceTable


def manuscript_facts(
    artifacts: Any, ledger: Any, reviews: Any, run: Any, run_id: str
) -> ManuscriptFacts:
    """本 run 的持久事实 → 手稿输入（每条都经既有读面）。"""
    evidence = evidence_of_run(ledger, run_id)
    return ManuscriptFacts(
        inputs=report_inputs(artifacts, ledger, reviews, run, run_id),
        references=reference_table(artifacts, tool_evidence(evidence)),
    )


__all__ = ["ManuscriptFacts", "manuscript_facts"]
