"""**被评对象** → 评审者提示词的**装配面**（GOAL-20261020-091 EC-02；产品路径）。

把**既有**装配器（`run_orchestration/review_material.build_review_material`）包成组合根能用
的**一行闭包**，与 `retrieval_context_support.retrieval_context_builder` /
`report_support.report_task_runner` **同形同层**。

**为什么需要这一层**：装配器需要 `(workflow, artifacts)` 两件事实（解析产出方的真实任务
身份 + 读那件制品），而组合根的编排依赖里只有 Port 聚合 —— 把「用哪两件 Port」这个装配
决策收在一处（两个组合根**只差 Port 实例**），与 `session_tool_support` 收拢注册面是
同一个理由：多一个入口就多一次漂移机会。

**默认行为逐字不变**：闭包只在组合根**显式**接上时生效（`review_material=None` ⇒ 提示词
里没有那一段）；且**只有评审者**会挂（`review_material.is_reviewer` 判，非评审 phase
连装配器都不调用）。**只读 canonical、零出网**：本模块不构造任何客户端。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def review_material_builder(ports: Any) -> Callable[[Any, Any], Any]:
    """从**组合根的 Port 聚合**取两件事实（`workflow` / `artifacts`）并造闭包。

    为什么传整个 `ports` 而不是两个关键字参数：组合根有 450 行硬上限，而「用哪两件 Port」
    这件事收在本模块里就够了 —— 多点一次名会让组合根多一行，那正是既有模块撞线的形态。
    取法是**属性访问**（两个组合根的聚合都有这两个字段，见 `_SqliteStoreParts` 与
    `pg_composition` 的 `c` 字典包装）；取不到 ⇒ `AttributeError` 在装配期**响亮**失败
    （不静默给一个没有 workflow 的装配器 —— 那会让「声明了跨相输入的评审 phase」在
    运行期才点名失败）。
    """
    return _builder(workflow=_field(ports, "workflow"), artifacts=_field(ports, "artifacts"))


def _field(ports: Any, name: str) -> Any:
    """聚合面上的一个字段（dict 与 dataclass 两种聚合形态都认）。"""
    if isinstance(ports, dict):
        return ports[name]
    return getattr(ports, name)


def _builder(*, workflow: Any, artifacts: Any) -> Callable[[Any, Any], Any]:
    """`(task, declared_cross_phase_inputs) -> ReviewMaterialView` 的闭包。

    `workflow` / `artifacts` 是组合根持有的**同一实例**（与执行面同源 ⇒ 解出来的产出方
    任务身份就是本 run 真的注册过的那一个）。`workflow` 缺省 `None` ⇒ 装配器对**声明了**
    跨相输入的评审 phase **点名失败**（不静默给空段：「读不到」与「没有」必须分得开）。
    """
    from packages.application.run_orchestration.review_material import build_review_material

    def build(task: Any, declared: Any) -> Any:
        return build_review_material(workflow, artifacts, task, declared)

    return build


__all__ = ["review_material_builder"]
