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
    """本请求匹配到的路由**自己声明**的查询参数集（非读面 / 未声明 ⇒ `None`）。

    `None` 与空集**语义不同**：`None` = 该路由不在射程内（一字不动）；空集 = 在射程内
    但无参数（同样跳过）。都跳过，但区分开是为了让「为什么没管」可读。
    """
    if request.method not in _READ_METHODS:
        return None
    route = request.scope.get("route")
    dependant = getattr(route, "dependant", None)
    if dependant is None:
        return None
    return frozenset(field.alias for field in dependant.query_params)


def reject_unknown_query_params(request: Request) -> None:
    """未知查询参数 ⇒ **422 + 逐个点名 + 该路由的已知集**（供调用方自纠）。"""
    known = declared_query_params(request)
    if not known:
        return
    unknown = sorted(set(request.query_params.keys()) - known)
    if not unknown:
        return
    raise ApiError(
        422,
        "Unknown Query Parameter",
        f"unknown query parameter(s): {', '.join(unknown)} (known: {', '.join(sorted(known))})",
    )


__all__ = ["declared_query_params", "reject_unknown_query_params"]
