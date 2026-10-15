"""臂间**可比**：同一 run 的两个臂在同一指标上的**差值**（GOAL-20261015-079 EC-03）。

**它补哪一格**：EC-02 让两个臂各自落库（读面上有两条记录），但「**两臂差多少**」——
研究人员真正要看的那个数 —— 没有任何面。本模块把它算成**可复核的事实**。

**三条纪律**（逐条都可判）：

1. **差由落库值算**（不是重跑一遍实验，也不是估）：输入就是读面给的 `metrics` 字典；
2. **同名列才比**：只在**两侧都有的**指标上求差；**缺指标 ⇒ 不算 0**（把「没测」当成
   「测出 0」会伪造一个很大的差值）；
3. **缺指标点名**：两侧各自的缺口**逐条列出**（`missing_in_<arm>`），读者能看出
   「是这次没测」还是「两臂测的不是同一批指标」。

**为什么不在域里**：差值不是**持久事实**（它随时可由两条记录重算），把它写进域会让
「同一份落库状态」有两个真相。本模块是**纯函数**（输入两份指标映射 ⇒ 输出差值读数），
落在 application 层，与 `report_facts.metrics_of` 同一层。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class MetricDelta:
    """一个指标在两臂上的读数与差值（**逐字保留**原值与来源臂名）。"""

    metric: str
    left_arm: str
    right_arm: str
    left_value: str
    right_value: str
    #: `right - left`（**右臂减左臂**；符号约定写在这里，不打哑谜）。
    delta: str


@dataclass(frozen=True, slots=True)
class ArmComparison:
    """两臂的对比读数：可比指标 + **缺指标（逐臂点名）** + 不可比指标。"""

    left_arm: str
    right_arm: str
    deltas: tuple[MetricDelta, ...] = field(default_factory=tuple)
    #: 左臂**缺**的指标名（逐条点名；它们**不**参与差值）。
    missing_in_left: tuple[str, ...] = field(default_factory=tuple)
    #: 右臂**缺**的指标名。
    missing_in_right: tuple[str, ...] = field(default_factory=tuple)
    #: 两侧都有、但**不是数**的指标（逐条点名；它们**不**参与差值）。
    not_numeric: tuple[str, ...] = field(default_factory=tuple)

    @property
    def comparable(self) -> bool:
        """有没有**至少一个**可比指标（空集合 ⇒ 这次对比没有内容，不作结论）。"""
        return bool(self.deltas)


def compare_arms(
    left_arm: str,
    left_metrics: Mapping[str, Any],
    right_arm: str,
    right_metrics: Mapping[str, Any],
) -> ArmComparison:
    """两臂指标 → 对比读数（纯函数；**缺指标点名、不折算成 0**）。

    `left` / `right` 是**臂名**（调用方从读面拿；本函数不猜哪个是对照）——
    「哪个是基准」是**声明**的事（EC-02 的臂声明顺序），本函数只做算术。
    """
    left_names = set(left_metrics)
    right_names = set(right_metrics)
    deltas: list[MetricDelta] = []
    not_numeric: list[str] = []
    for name in sorted(left_names & right_names):
        left_value = left_metrics[name]
        right_value = right_metrics[name]
        left_decimal = _as_decimal(left_value)
        right_decimal = _as_decimal(right_value)
        if left_decimal is None or right_decimal is None:
            # 两侧都在、但不是数（布尔 / 字符串 / 嵌套对象）⇒ **点名**，不算差。
            not_numeric.append(name)
            continue
        deltas.append(
            MetricDelta(
                metric=name,
                left_arm=left_arm,
                right_arm=right_arm,
                left_value=_text(left_value),
                right_value=_text(right_value),
                delta=_text(right_decimal - left_decimal),
            )
        )
    return ArmComparison(
        left_arm=left_arm,
        right_arm=right_arm,
        deltas=tuple(deltas),
        missing_in_left=tuple(sorted(right_names - left_names)),
        missing_in_right=tuple(sorted(left_names - right_names)),
        not_numeric=tuple(not_numeric),
    )


def _as_decimal(value: Any) -> Decimal | None:
    """值 → `Decimal`（**不是数** ⇒ `None`；不把布尔当 0/1 —— 那会伪造差值）。

    `bool` 在这里**不是**数：`True - False = 1` 是算术上成立、语义上荒唐的比较
    （「两臂的 agreement 差 1」）。布尔指标要对比就**另立**比较口径，不混进数值差。
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, Decimal)):
        return Decimal(str(value))
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, str):
        try:
            return Decimal(value.strip())
        except (InvalidOperation, ValueError):
            return None
    return None


def _text(value: Any) -> str:
    """值 → 逐字文本（读数里保留原形态：`7990.0` 不写成 `7990`）。"""
    if isinstance(value, Decimal):
        return format(value.normalize(), "f") if not value.is_zero() else "0"
    return str(value)


__all__ = ["ArmComparison", "MetricDelta", "compare_arms"]
