"""检索内容 → 会话上下文的**装配面**（GOAL-20261014-078 EC-01；产品路径）。

把**既有**装配器（`run_orchestration/retrieval_context.build_retrieval_context`）包成
两个组合根都能用的**一行闭包**，与 `report_support.report_task_runner` /
`experiment_support.sandbox_experiment_runner` **同形同层**。

**为什么需要这一层**：装配器需要 `(artifacts, ledger, run_id)` 三件事实，而组合根的
编排依赖里只有 Port 聚合 —— 把「用哪两件 Port」这个装配决策收在一处（两个组合根**只差
Port 实例**），与 `session_tool_support` 收拢注册面是同一个理由：多一个入口就多一次漂移机会。

**默认行为逐字不变**：闭包只在组合根**显式**接上时生效（`retrieval_context=None` ⇒
会话不带检索上下文）。**只读 canonical、零出网**：本模块不构造任何客户端。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def retrieval_context_builder(
    *,
    artifacts: Any,
    ledger: Any,
) -> Callable[[str], Any]:
    """`(run_id) -> RetrievalContextView` 的闭包（两个组合根共用这一处装配决策）。

    `artifacts` / `ledger` 是组合根持有的**同一实例**（与写面同源 ⇒ 读的是刚落库的证据）。
    """
    from packages.application.run_orchestration.retrieval_context import (
        build_retrieval_context,
    )

    def build(run_id: str) -> Any:
        return build_retrieval_context(artifacts, ledger, run_id)

    return build


__all__ = ["retrieval_context_builder"]
