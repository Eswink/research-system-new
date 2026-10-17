"""前序知识 → 会话上下文的**装配面**（GOAL-20261018-082 EC-01；产品路径）。

把**既有**装配器（`run_orchestration/prior_knowledge.build_prior_knowledge`）包成组合根能用的
**一行闭包**，与 `retrieval_context_support.retrieval_context_builder` /
`report_support.report_task_runner` / `experiment_support.sandbox_experiment_runner`
**同形同层**。

**为什么需要这一层**：装配器需要 `(memory_store, now)` 两件事实，而编排依赖里只有 Port 聚合 ——
把「用哪个 store、取什么时刻」这个装配决策收在一处（两个组合根只差实例），与
`retrieval_context_builder` 是同一个理由：多一个入口就多一次漂移机会。

**默认行为逐字不变**：闭包只在组合根**显式**接上时生效（`prior_knowledge=None` ⇒
会话不带前序知识）。**只读 canonical、零出网**：本模块不构造任何客户端。

**`now` 的口径**：装配器**不读进程时钟**（那会让同一份持久状态给出不同视图）；
时刻由本闭包在**每次求值**时取一次并传进去 —— 时钟只在最外层读，内层是纯函数。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def prior_knowledge_builder(*, memory_store: Any) -> Callable[[str], Any]:
    """`(run_id) -> PriorKnowledgeView` 的闭包（两个组合根共用这一处装配决策）。

    `memory_store` 是组合根持有的**同一实例**（与写面同源 ⇒ 读的是刚落库的记忆）。
    """
    from packages.application.run_orchestration.prior_knowledge import build_prior_knowledge
    from packages.domain.core import Timestamp

    def build(run_id: str) -> Any:
        return build_prior_knowledge(memory_store, now=Timestamp.now(), run_id=run_id)

    return build


__all__ = ["prior_knowledge_builder"]
