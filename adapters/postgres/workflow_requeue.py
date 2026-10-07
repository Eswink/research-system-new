"""PostgresWorkflowEngine 的人工恢复面（ADR-0033；与 `SqliteWorkflowOps` 同形的拆分）。

从 `workflow_engine.py` 拆出来（该文件触到 450 行硬上限），**逐行搬运**、语义不改：
mixin 由 `PostgresWorkflowEngine` 继承；依赖宿主（`PostgresAdapterBase` / engine
`__init__`）提供的 `_conn / _outbox / _record / _ensure_open / _wrap_operational /
_telemetry`。判据在 `adapters/postgres/workflow_ops.py::requeue_impl`（纯函数接连接与
记账回调，与 SQLite 侧 `requeue_task` 同判据）。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import psycopg

from packages.application.observability.scope import operation
from packages.application.observability.signals import CorrelationRef, OperationScope
from packages.application.ports.errors import InvalidInputError


class PostgresRequeueOps:
    """宿主提供（PostgresAdapterBase / engine __init__）。"""

    _conn: Any
    _outbox: Any
    _telemetry: Any
    _ensure_open: Callable[[], None]
    _record: Callable[..., None]
    _wrap_operational: Callable[[Exception], Exception]

    def requeue(self, task_id: str) -> str:
        """人工恢复一条 `DEAD_LETTER` 任务（ADR-0033 / AGENTS.md §7）；成功返回 `restored`。

        与 SQLite 侧同判据（`workflow_ops.requeue_impl`）：目标状态取自 domain 状态机，
        落库与事件同事务；任务不存在 / 状态不是 `DEAD_LETTER`（含「已恢复」）⇒ 点名拒绝。
        """
        with operation(
            self._telemetry,
            scope=OperationScope.WORKFLOW_QUEUE,
            name="workflow.requeue",
            correlation=CorrelationRef(task_id=task_id),
        ):
            self._ensure_open()
            try:
                from adapters.postgres.workflow_ops import requeue_impl

                return requeue_impl(self._conn, self._record, self._outbox, task_id)
            except InvalidInputError:
                raise
            except psycopg.OperationalError as exc:
                raise self._wrap_operational(exc) from exc
