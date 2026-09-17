"""每线程连接的 SQLite 控制面入口（GOAL-004 cycle 5 = EC-05）。

背景：控制面把一个连接对象注入所有 store，而 FastAPI 的同步端点跑在 threadpool 里、
调度守护线程也在写。`SerializedConnection` 用一把可重入锁把语句级与事务级串行化
（PLAN-20260915-070/076），但那仍是**一条连接被多个线程共用**：`check_same_thread=False`
只关掉了检查，任何绕过锁的入口、以及"写后立读"的可见性问题都还在（RECHECK-070 的告警）。

本模块把控制面的锁粒度落到**每条线程一条连接**：

- 文件库（真实部署与 live e2e）：每条线程第一次用到时开自己的一条（WAL +
  `busy_timeout`，与 `db.connect` 同一套参数）；跨线程写由 SQLite 自身的 WAL 写锁 +
  `busy_timeout` 协调，不再靠"一把大锁把所有人串起来"；
- `:memory:`（仅测试）：SQLite 的内存库**属于连接**，每线程一条会各自看到空库，
  所以这种路径共用一条连接（`db.connect` 的原行为）——这是 SQLite 语义，不是妥协；
- `close()` 关本线程连接（与 sqlite3 语义一致），`close_all()` 关掉登记过的全部连接
  （应用关闭路径用它，替代原来"关掉唯一那条"）。

`ThreadLocalConnection` 是共享连接对象的**代理面**：store 代码零改动——连接上除
`with` 块与 `row_factory` 写回之外的一切入口都由 `__getattr__` 转发到本线程连接。
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any

from adapters.sqlite.db import connect

_MEMORY_PATHS = frozenset({":memory:", ""})


def is_memory_path(db_path: str | Path) -> bool:
    """`:memory:` 形式（含空串）——这些库只能共用一条连接，见模块文档。"""
    text = str(db_path)
    return text in _MEMORY_PATHS or ":mode=memory" in text


class ThreadLocalConnection:
    """每线程一条真实连接；对外仍是一个连接对象（代理面）。

    线程第一次用到时才开连接（懒创建）：只读探测线程、短命线程不会留下空连接。
    连接按登记顺序保存在 `_connections` 里，`close_all()` 关闭它们。
    """

    def __init__(self, db_path: str | Path, *, journal_mode: str = "WAL") -> None:
        self._db_path = str(db_path)
        self._journal_mode = journal_mode
        self._local = threading.local()
        self._registry_lock = threading.Lock()
        self._connections: list[sqlite3.Connection] = []
        # 内存库只能共用一条：每条线程一条会各自看到空库（SQLite 语义）。
        shared = connect(db_path, journal_mode=journal_mode) if is_memory_path(db_path) else None
        self._shared = shared
        if shared is not None:
            self._connections.append(shared)

    @property
    def db_path(self) -> str:
        return self._db_path

    def current(self) -> sqlite3.Connection:
        """当前线程的连接（内存库场景永远是那条共享连接）。"""
        shared = self._shared
        if shared is not None:
            return shared
        connection = getattr(self._local, "connection", None)
        if connection is None:
            connection = connect(self._db_path, journal_mode=self._journal_mode)
            self._local.connection = connection
            with self._registry_lock:
                self._connections.append(connection)
        return connection

    def __getattr__(self, name: str) -> Any:
        """其余连接入口转发到本线程连接（语句、游标、事务边界、pragma 面）。

        不逐个写转发方法：store 用到的面比我们记得的多（`total_changes`、
        `in_transaction` 之类），而每写一个转发方法就是一处将来会漏的地方。
        下划线开头的名字不转发（否则 `current()` 里的属性缺失会递归）。
        """
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(self.current(), name)

    @property
    def row_factory(self) -> Any:
        return self.current().row_factory

    @row_factory.setter
    def row_factory(self, value: Any) -> None:
        self.current().row_factory = value

    def __enter__(self) -> ThreadLocalConnection:
        """`with conn:` = 本线程连接的事务块（与 sqlite3 语义一致）。"""
        self.current().__enter__()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> Any:
        return self.current().__exit__(exc_type, exc, tb)

    def close(self) -> None:
        """关本线程连接（sqlite3 语义）；应用关闭用 `close_all()`。"""
        self.current().close()

    def close_all(self) -> int:
        """关闭登记过的全部连接（`check_same_thread=False` 允许跨线程关闭）。"""
        with self._registry_lock:
            connections, self._connections = self._connections, []
        for connection in connections:
            connection.close()
        return len(connections)

    def connection_count(self) -> int:
        """已开连接数（观测用：每线程一条时随线程数增长）。"""
        with self._registry_lock:
            return len(self._connections)


__all__ = ["ThreadLocalConnection", "is_memory_path"]
