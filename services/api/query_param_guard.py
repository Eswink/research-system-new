"""未知查询参数的**通用**守卫（GOAL-20261013-069 EC-02）。

**为什么需要它**：序 36 只在**记忆读面**立了这条纪律（射程**有意**收窄）。**实测**：
全仓 9 条 GET 声明了查询参数，其中 `GET /notifications?limt=5`（正确名 `limit`）与
`GET /projects/{id}/cost-forecast?horizon_day=7`（正确名 `horizon_days`）**照样 200**
（静默吞掉，用的是默认值）—— 调用方**以为设了参数**。本模块把纪律**机械扩到全体**。

**已知集从签名导出（D-1）**：从**匹配到的路由**自己的 `dependant.query_params` 读
（`request.scope["route"]`）—— **不是**手写清单 ⇒ 加参数**自动**跟着走，不会漂
（手写清单会漂：加参数忘改 ⇒ 正确请求被误拒）。

**机制（D-5，实测选定）**：注册为**应用级依赖**（`FastAPI(dependencies=[...])`）——
依赖在**路由匹配之后**才解析 ⇒ 能看见**该路由**自己的声明面；而中间件在匹配**之前**
运行（读不到路由）。**实测**：构造期声明生效、事后 `router.dependencies.append`
**不**生效（装配顺序 = 契约的一部分）。

**射程（有意边界）**：**只**在「声明了查询参数」的读面路由（GET/HEAD）上生效；
**未声明**参数的路由**一字不动** —— 那种面没有「已知集」可言（另成一面，登记为
后续候选，承序 36 的既有登记）。
"""

from __future__ import annotations

from fastapi import Request

from services.api.errors import ApiError

#: 读面方法（GET 路由在 Starlette 下同时接受 HEAD）。
_READ_METHODS: frozenset[str] = frozenset({"GET", "HEAD"})


def declared_query_params(request: Request) -> frozenset[str] | None:
    """本请求匹配到的路由**自己声明**的查询参数集（非读面 ⇒ `None`）。

    `None` 与空集**语义不同**（GOAL-20261013-072 把这条区分用起来）：
    `None` = 该路由**不在射程内**（非读面 ⇒ 一字不动）；空集 = **读面但无声明**
    ⇒ 该路由**不接受任何**查询参数（收到即 422 点名，见下）。
    """
    if request.method not in _READ_METHODS:
        return None
    route = request.scope.get("route")
    dependant = getattr(route, "dependant", None)
    if dependant is None:
        return None
    return frozenset(field.alias for field in dependant.query_params)


def reject_unknown_query_params(request: Request) -> None:
    """未知查询参数 ⇒ **422 + 逐个点名 + 该路由的已知集**（供调用方自纠）。

    **两种形态**（同一纪律的两个分支）：

    - **已声明**的路由（已知集非空）：不在集里的 ⇒ 点名（序 37 起）；
    - **未声明**的路由（已知集**空**）：**任何**查询参数都点名，并**明写该路由不接受
      查询参数**（空集的「已知集」清单是空串 ⇒ 正文要说清楚，否则读者以为漏了清单）。
      GOAL-20261013-072：「静默吞掉」族的**最后一面**（此前这类路由收到查询串照样 200）。

    **射程**：非读面（`None`）**一字不动** —— 写面按序 39 的 DTO 纪律处理。
    """
    known = declared_query_params(request)
    if known is None:
        return  # 非读面 ⇒ 不在射程
    unknown = sorted(set(request.query_params.keys()) - known)
    if not unknown:
        return
    if not known:
        raise ApiError(
            422,
            "Unknown Query Parameter",
            f"unknown query parameter(s): {', '.join(unknown)}"
            " (this route accepts no query parameters)",
        )
    raise ApiError(
        422,
        "Unknown Query Parameter",
        f"unknown query parameter(s): {', '.join(unknown)} (known: {', '.join(sorted(known))})",
    )


__all__ = ["declared_query_params", "reject_unknown_query_params"]
