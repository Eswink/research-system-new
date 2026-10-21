"""会话提示词三段的**取值面**（自 `task_executor.py` 拆出：规模门 + GOAL-089 EC-02）。

三段**并列**、各自缺席也各自成立：

- **方向**（GOAL-20261019-089 EC-02）：项目声明的研究方向 —— 「被要求研究什么」；
- **前序知识**（GOAL-20261018-082 EC-01）：跨 run 的受治记忆 —— 「已经知道什么」；
- **检索摘录**（GOAL-20261016-081 EC-01）：本 run 系统取得的内容 —— 「这一轮取回了什么」；
- **被评对象**（GOAL-20261020-091 EC-02）：本 phase 声明的上游产物 —— 「你要判的是这一件东西」。

三者的渲染器都是**纯函数**（`retrieval_prompt` 里各一个），本模块只做「装配结果视图 →
那段文本 / `None`」的取值：`None` 表示**那一槽位没接**，提示词因此**逐字节**等于既有形态
（这是三段共同的零回归口径）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # 只为类型：避免与 task_executor 形成导入环
    from packages.application.run_orchestration.task_executor import SessionSpecContext


def retrieval_prompt(spec_context: "SessionSpecContext") -> str | None:
    """检索摘录 → 提示词那一段；**缺省 `None` ⇒ `None`**（不加那一段）。"""
    view = spec_context.retrieval_context
    if view is None:
        return None
    from packages.application.run_orchestration.retrieval_prompt import render_retrieval_prompt

    return render_retrieval_prompt(view) or None


def prior_knowledge_prompt(spec_context: "SessionSpecContext") -> str | None:
    """前序知识 → 提示词那一段；**缺省 `None` ⇒ `None`**。"""
    view = spec_context.prior_knowledge
    if view is None:
        return None
    from packages.application.run_orchestration.retrieval_prompt import (
        render_prior_knowledge_prompt,
    )

    return render_prior_knowledge_prompt(view) or None


def review_material_prompt(spec_context: "SessionSpecContext") -> str | None:
    """**被评对象** → 提示词那一段；**缺省 `None` ⇒ `None`**（不加那一段）。"""
    view = spec_context.review_material
    if view is None:
        return None
    from packages.application.run_orchestration.retrieval_prompt import (
        render_review_material_prompt,
    )

    return render_review_material_prompt(view) or None


def direction_prompt(spec_context: "SessionSpecContext") -> str | None:
    """研究方向 → 提示词那一段；**未声明 ⇒ `None`**（提示词逐字不变）。"""
    from packages.application.run_orchestration.retrieval_prompt import render_direction_prompt

    return render_direction_prompt(spec_context.direction) or None


def review_outcome_prompt(spec_context: "SessionSpecContext") -> str | None:
    """**上一轮评审结论** → 提示词那一段；**缺省 `None` ⇒ `None`**（不加那一段）。"""
    view = spec_context.review_outcome
    if view is None:
        return None
    from packages.application.run_orchestration.retrieval_prompt import (
        render_review_outcome_prompt,
    )

    return render_review_outcome_prompt(view) or None


__all__ = [
    "direction_prompt",
    "prior_knowledge_prompt",
    "retrieval_prompt",
    "review_material_prompt",
    "review_outcome_prompt",
]
