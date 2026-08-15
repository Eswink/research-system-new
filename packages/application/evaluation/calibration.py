"""M11 Human Calibration：human judgment vs machine judgment 对比。

约束：
- calibration sample 只用于分析（agreement/FP/FN/ambiguity），不用于
  修改 Reviewer 实现或拟合阈值；
- false positive = machine PASS 但 human FAIL；
- false negative = machine FAIL 但 human PASS；
- ambiguous = human 标记 AMBIGUOUS；
- 纯函数、frozen 输入。
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from packages.domain.eval_result import ReviewerVerdict


@dataclass(frozen=True, slots=True)
class CalibrationSample:
    """一条校准样本：case 引用 + human/machine 判断。"""

    sample_id: str
    human: ReviewerVerdict
    machine: ReviewerVerdict
    note: str = ""


@dataclass(frozen=True, slots=True)
class CalibrationReport:
    """校准对比结果；只报告统计，不做任何自动修正。"""

    total: int
    agreements: int
    disagreements: int
    false_positives: tuple[str, ...]
    false_negatives: tuple[str, ...]
    ambiguous: tuple[str, ...]

    @property
    def agreement_rate(self) -> str:
        if self.total == 0:
            return "0"
        return str(Decimal(self.agreements) / Decimal(self.total))


def calibrate(samples: tuple[CalibrationSample, ...]) -> CalibrationReport:
    """对比 human 与 machine 判断；AMBIGUOUS 不参与 agreement 判定。"""

    agreements = 0
    disagreements = 0
    false_positives: list[str] = []
    false_negatives: list[str] = []
    ambiguous: list[str] = []
    for sample in samples:
        if sample.human is ReviewerVerdict.AMBIGUOUS or sample.machine is ReviewerVerdict.AMBIGUOUS:
            ambiguous.append(sample.sample_id)
            continue
        if sample.human is sample.machine:
            agreements += 1
        else:
            disagreements += 1
            if sample.machine is ReviewerVerdict.PASS:
                false_positives.append(sample.sample_id)
            else:
                false_negatives.append(sample.sample_id)
    return CalibrationReport(
        total=len(samples),
        agreements=agreements,
        disagreements=disagreements,
        false_positives=tuple(false_positives),
        false_negatives=tuple(false_negatives),
        ambiguous=tuple(ambiguous),
    )
