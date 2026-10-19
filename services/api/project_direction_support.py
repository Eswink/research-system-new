"""项目方向 → 会话提示词的**装配面**（GOAL-20261019-089 EC-02；产品路径）。

把 canonical 的项目注册条目（`ProjectStore`）包成组合根能用的一行闭包，与
`prior_knowledge_support.prior_knowledge_builder` / `retrieval_context_support` **同形同层**：
两个组合根只差 Port 实例，装配决策只此一份（多一个入口就多一次漂移机会）。

**读的是 canonical**：`ProjectStore.get_project(project_id)` —— 与
`GET /projects/{id}` 同一条读面、同一个对象；不复制、不缓存（改方向立刻对下一次 run 生效）。

**三种形态分得开**（与 `ProjectDefinition.direction` 的三态同口径）：

- store 未配置 / 项目不存在 ⇒ `None`（**未声明**：不是错误，默认项目由 examples 合约合成，
  它没有方向行）；
- 行存在但 `direction is None` ⇒ `None`（未声明）；
- 行存在且声明了方向 ⇒ 那个字符串（逐字，不加工）。

**默认行为逐字不变**：闭包只在组合根**显式**接上时生效（`project_direction=None` ⇒
提示词里没有那一段）。**只读、零出网**：本模块不构造任何客户端。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def project_direction_builder(*, project_store: Any) -> Callable[[str], str | None]:
    """`(project_id) -> direction | None` 的闭包（两个组合根共用这一处装配决策）。"""

    def resolve(project_id: str) -> str | None:
        if project_store is None:
            return None
        try:
            project = project_store.get_project(project_id)
        except KeyError:
            # 未注册的项目：没有方向可读（由启动链自己的 404 语义负责点名）。
            return None
        direction = project.direction
        return direction if isinstance(direction, str) and direction.strip() else None

    return resolve


__all__ = ["project_direction_builder"]
