"""PostgresWorkflowEngine 的统一派发读面（GOAL-005 cycle 5 = EC-05 ①）。

与 `workflow_claim.py` / `workflow_ops.py` 同形：纯函数接连接、权威时钟与记账回调，
引擎侧只负责 `_ensure_open` 与错误边界。装配只有一处
（`projections.dispatch_ownership_many`）——单 run 读就是**批量读的一条**，两个入口
不会各有一套判据；本模块只决定"记哪一次账"。
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from adapters.postgres.projections import (
    dispatch_ownership_many as proj_dispatch_ownership_many,
)
from packages.application.ports.workflow_engine import DispatchOwnership

Record = Callable[..., None]


def dispatch_ownership_impl(
    conn: Any, record: Record, run_id: str, now: datetime
) -> DispatchOwnership:
    """单 run 读：与批量读同一段装配，按单 run 的名字记账。"""
    ownership = proj_dispatch_ownership_many(conn, (run_id,), now)[run_id]
    record("dispatch_ownership", run_id, result=ownership.kind)
    return ownership


def dispatch_ownership_many_impl(
    conn: Any, record: Record, run_ids: tuple[str, ...], now: datetime
) -> dict[str, DispatchOwnership]:
    """一批 run 的读面：两条 SQL（重排 + 租约）取整批，只记一次调用。"""
    ownerships = proj_dispatch_ownership_many(conn, run_ids, now)
    record("dispatch_ownership_many", f"n={len(ownerships)}")
    return ownerships
