"""记忆读面的**未知查询参数**守卫（GOAL-20261013-068 EC-02）。

**为什么单列**：`services/api/routers/memory.py` 有 **450 行硬上限**（规模门）—— 本轮的守卫
加进去后触顶 ⇒ 把它（连同已知集）**原样搬到这里**，并守住那道门。**语义一字未动**。

**为什么需要它**：此前打错名字的参数**照样 200 + 全量**（**实跑**：`?definitely_not_a_param=1`
⇒ 键仍只有 `['records','scope_note']`）⇒ 调用方**以为筛过了**而拿到的是全量
——「静默降级」的形态（承本战役「点名失败而非静默降级」的禁令）。

**射程（有意边界）**：本纪律**只**覆盖记忆读面的两个 GET（`/memory` 与 `/memory/validity`）——
全仓 **65** 条 GET 的「已知参数」口径**未定** ⇒ 扩散会撞出大量未定义行为（登记为后续候选）。

**多个未知 ⇒ 逐个点名**（只报第一个会让「还有哪些打错了」读不出来）。
"""

from __future__ import annotations

from fastapi import Request

from services.api.errors import ApiError

#: 记忆读面的**已知查询参数**（每加一个参数都要**显式**登记）。
_KNOWN_QUERY_PARAMS: frozenset[str] = frozenset({"scope", "proposed_by", "at"})


def reject_unknown_query_params(request: Request) -> None:
    """**未知查询参数 ⇒ 422 点名**（已知集一并给出，供调用方自纠）。

    **多个未知 ⇒ 逐个点名**（只报第一个会让「还有哪些打错了」读不出来）。
    """
    unknown = sorted(set(request.query_params.keys()) - _KNOWN_QUERY_PARAMS)
    if not unknown:
        return
    raise ApiError(
        422,
        "Unknown Query Parameter",
        f"unknown query parameter(s): {', '.join(unknown)}"
        f" (known: {', '.join(sorted(_KNOWN_QUERY_PARAMS))})",
    )


__all__ = ["reject_unknown_query_params"]
