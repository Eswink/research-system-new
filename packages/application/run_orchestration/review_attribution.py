"""评审判词的**归因面**：把「这条评审跑在哪个模型上」变成可读的一格（GOAL-20261018-085 EC-01）。

**它补哪一格**：落库的 `ReviewFinding.reviewed_by` 逐字是 `gate:<agent id>` —— **agent 名**。
GOAL-084 已证明 agent 名与底层模型可以**完全脱钩**（出厂目录里四个 ModelDefinition 曾共用
同一个 `model_name`）⇒ 只凭 agent 名，「这条评审是谁判的」不可归因。

**本模块只做一件事**：把**装配好的执行目标**折成稳定串形 `endpoint/model_name`
（与 `preflight/review_independence.describe_target` **同形态**）。

**为什么取 `SessionSpecContext.endpoint` / `.model` 而不是 `plan.resolved_models`**：
后者给的是 model **id**，而「是不是同一个底层模型」只有在 `(endpoint, model_name)` 上
才判得出来（GOAL-084 的核心读数）。

**边界**：任一字段缺失 ⇒ `None`。`None` = **未声明该面**，不是「同一个模型」，
也不得被读成「独立」—— 判据按 `None` 点名（见 `evaluation/panel_verdict`）。
"""

from __future__ import annotations

from typing import Any


def reviewer_model_of(spec_context: Any) -> str | None:
    """装配好的执行目标 → `endpoint/model_name`；任一缺失 ⇒ `None`。"""
    endpoint = getattr(spec_context, "endpoint", None)
    model = getattr(spec_context, "model", None)
    endpoint_id = getattr(endpoint, "id", None)
    model_name = getattr(model, "model_name", None)
    if not endpoint_id or not model_name:
        return None
    return f"{endpoint_id}/{model_name}"


__all__ = ["reviewer_model_of"]
