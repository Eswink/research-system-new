"""**上一轮评审结论** → 会话提示词的**装配面**（GOAL-20261022-093；产品路径）。

把**既有**装配器（`run_orchestration/review_outcome.build_review_outcome`）包成组合根能用
的**一行闭包**，与 `prior_knowledge_support.prior_knowledge_builder` /
`review_material_support.review_material_builder` **同形同层**。

**为什么需要这一层**：装配器需要 `(runs, findings)` 两件事实（run → 程序归属 → 前序 run →
它的落库判词），而组合根的编排依赖里只有 Port 聚合 —— 把「用哪两件 Port」这个装配决策
收在一处（两个组合根**只差实例**），与另两个 builder 是同一个理由：多一个入口就多一次
漂移机会。

**默认行为逐字不变**：闭包只在组合根**显式**接上时生效（`review_outcome=None` ⇒ 提示词
里没有那一段）。**只读 canonical、零出网、不读进程时钟**：本模块不构造任何客户端，
也不取「现在几点」（判词自带 `reviewed_at`，与提示词无关）。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def review_outcome_builder(ports: Any) -> Callable[[str], Any]:
    """从**组合根的 Port 聚合**取两件事实（`runs_store` / `review_findings`）并造闭包。

    取法与 `review_material_builder` 同一口径：**属性访问**优先（dataclass 聚合），
    也认 dict 聚合（`pg_composition` 的 `c` 就是字典）。取不到 ⇒ `KeyError` /
    `AttributeError` 在**装配期**响亮失败 —— 不静默给一个读不到判词的装配器（那会让
    「上一轮被判过」与「读不到」在运行期才不可分辨）。
    """
    return _builder(runs=_field(ports, "runs_store"), findings=_field(ports, "review_findings"))


def _field(ports: Any, name: str) -> Any:
    """聚合面上的一个字段（dict 与 dataclass 两种聚合形态都认）。"""
    if isinstance(ports, dict):
        return ports[name]
    return getattr(ports, name)


def _builder(*, runs: Any, findings: Any) -> Callable[[str], Any]:
    """`(run_id) -> ReviewOutcomeView` 的闭包。

    两件 Port 是组合根持有的**同一实例**（与执行面同源 ⇒ 读到的判词就是刚落库的那些）。
    """
    from packages.application.run_orchestration.review_outcome import build_review_outcome

    def build(run_id: str) -> Any:
        return build_review_outcome(runs, findings, run_id=run_id)

    return build


__all__ = ["review_outcome_builder"]
