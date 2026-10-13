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

**射程（有意边界，逐面演进）**：序 37（已声明读面）→ 序 40（未声明读面）→
序 41（写面）→ **序 42（重复形态，本轮的第四面）**。**`list` 声明**的参数
（`/evaluations/trend?expected_digests`）**合法重复**（web 客户端循环追加）
⇒ 重复纪律只覆盖**标量声明**。
"""

from __future__ import annotations

import inspect

from fastapi import Request

from services.api.errors import ApiError


def declared_query_params(request: Request) -> frozenset[str] | None:
    """本请求匹配到的路由**自己声明**的查询参数集（无法解析路由 ⇒ `None`）。

    三态语义（逐条，GOAL-20261013-072/073 把它用起来）：

    - `None` = **路由无法解析**（不在射程：没有 `route`/`dependant` 的边缘请求）；
    - 空集 = 路由**声明零个**查询参数 ⇒ **不接受任何**查询参数（收到即 422 点名）；
    - 非空集 = 该路由的已知集（不在集里的 ⇒ 点名）。

    **GOAL-20261013-073**：非读面（写面）此前被**提前返回 `None`** 而跳过 ——
    本轮去掉那个闸门 ⇒ 写面同样走「声明零个 ⇒ 不接受任何」那支（**实测**：63 条非读面
    路由**全部**声明 0 个查询参数；写面带查询参数此前**照样成功**：POST ⇒ 201、PATCH ⇒ 200）。
    """
    route = request.scope.get("route")
    dependant = getattr(route, "dependant", None)
    if dependant is None:
        return None
    return frozenset(field.alias for field in dependant.query_params)


def scalar_query_params(request: Request) -> frozenset[str]:
    """本请求匹配到的路由里**声明为标量**的查询参数（`list[...]` 声明**不算**）。

    **为什么需要**（GOAL-20261013-074）：`list` 声明的参数**合法重复**
    （**实测**：`/evaluations/trend?expected_digests` 声明 `list[str] | None`，
    web 客户端 `params.append(...)` 循环追加 ⇒ 重复是**契约**）；而**标量**声明
    重复时框架**静默取末值**（`?limit=1&limit=2` ⇒ 200，无披露）。
    ⇒ 重复纪律只覆盖标量。

    **判型面（实测选定）**：`scope["route"].endpoint` 的**签名注解**
    （`list[str] | None` vs `int`）—— `dependant.query_params` 的 `ModelField`
    在本版 FastAPI 上 `type_`/`annotation` 都是 `None`（实测），注解面是**可靠**的。
    """
    route = request.scope.get("route")
    endpoint = getattr(route, "endpoint", None)
    if endpoint is None:
        return frozenset()
    try:
        signature = inspect.signature(endpoint)
    except (TypeError, ValueError):
        return frozenset()
    return frozenset(
        name
        for name, parameter in signature.parameters.items()
        if "list[" in str(parameter.annotation)
    )


def reject_unknown_query_params(request: Request) -> None:
    """未知查询参数 ⇒ **422 + 逐个点名 + 该路由的已知集**（供调用方自纠）。

    **三种形态**（同一纪律的分支）：

    - **已声明**的路由（已知集非空）：不在集里的 ⇒ 点名（序 37 起）；
    - **零声明**的路由（已知集**空**）：**任何**查询参数都点名，并**明写该路由不接受
      查询参数**（空集的「已知集」清单是空串 ⇒ 正文要说清楚，否则读者以为漏了清单）。
      GOAL-20261013-072 接通**读面**；**GOAL-20261013-073** 接通**写面**
      （「静默吞掉」族的**第五面**；此前写面带查询串照样 201/200）。

    **射程**：路由**无法解析**（`None`）⇒ 一字不动（没有可判的声明面）。
    """
    known = declared_query_params(request)
    if known is None:
        return  # 路由无法解析 ⇒ 不在射程
    unknown = sorted(set(request.query_params.keys()) - known)
    if not unknown:
        repeated = _repeated_scalar_params(request, known)
        if repeated:
            raise ApiError(
                422,
                "Repeated Query Parameter",
                f"repeated query parameter(s): {', '.join(repeated)}"
                " (scalar parameters accept exactly one value)",
            )
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


def _repeated_scalar_params(request: Request, known: frozenset[str]) -> list[str]:
    """已知参数里**重复出现**的**标量**声明（`list` 声明的排除在外）。

    **必须用 `multi_items()`**（实测更正）：Starlette 的 `QueryParams.keys()`
    **去重**（同一个键出现两次时 `keys()` 只出一个）⇒ 用 `keys()` 计数
    永远数不到 1 以上（首版实现即此误 ⇒ 按压面假绿）。
    """
    list_declared = scalar_query_params(request)
    counts: dict[str, int] = {}
    for key, _ in request.query_params.multi_items():
        counts[key] = counts.get(key, 0) + 1
    return sorted(
        key
        for key, count in counts.items()
        if count > 1 and key in known and key not in list_declared
    )


__all__ = ["declared_query_params", "reject_unknown_query_params", "scalar_query_params"]
