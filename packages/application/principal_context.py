"""请求级主体上下文（application 层；**不**依赖 Web 框架）。

用途（GOAL-20260926-019 EC-01）：把「**这一次调用是谁发起的**」从入口层
（HTTP 中间件，认证通过后）传到**发布 canonical 事件的读点**，使
`EventEnvelope.actor` 记的是**真实主体**而不是占位常量。

为什么是环境式（contextvar）而不是显式参数：
`RunOrchestrationService` 与其 `EventSink` 是**应用级单例**（组合根构造一次），
而主体是**每次请求各不相同**的。改它的构造/调用签名会把 principal 穿进几十个
调用点并顶到零余量文件（`composition.py` / `run_orchestration/service.py` 各 450 行）；
环境式上下文让**读点**一处生效、**缺省时逐字回退**，占用面最小。

**向后兼容是硬约束**：本模块的缺省值是 `None`，读点必须把 `None` 解释为
「没有请求主体」并**沿用调用方既有的常量**（`default_actor` / `"user:console"`）
⇒ 未启用认证时既有行为**逐字不变**。

边界：本模块只承载**请求期**的主体；它**不是**授权判定，也**不**做角色 / 权限
（M18）。异步传播：入口层在 `call_next` **之前**设置、在响应之后重置，
下游处理与该次请求同任务上下文可见。
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Iterator

from packages.domain.principal import Principal

_CURRENT: ContextVar[Principal | None] = ContextVar("researchos_current_principal", default=None)


def current_principal() -> Principal | None:
    """当前请求的主体；`None` = 本次调用没有主体（如未启用认证、后台线程）。"""
    return _CURRENT.get()


def set_current_principal(principal: Principal | None) -> Token[Principal | None]:
    """设置当前主体，返回可用于复原的 token（调用方负责复原）。"""
    return _CURRENT.set(principal)


def reset_current_principal(token: Token[Principal | None]) -> None:
    """按 token 复原（与 `set_current_principal` 成对，放在 `finally` 里）。"""
    _CURRENT.reset(token)


@contextmanager
def principal_scope(principal: Principal | None) -> Iterator[None]:
    """`with` 形态的作用域（用例与后台任务用；异常也会复原）。"""
    token = set_current_principal(principal)
    try:
        yield
    finally:
        reset_current_principal(token)


__all__ = [
    "current_principal",
    "principal_scope",
    "reset_current_principal",
    "set_current_principal",
]
