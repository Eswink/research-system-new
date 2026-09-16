"""共享连接的两个游标面：物化视图与自建游标包装。

从 `adapters/sqlite/db.py` 拆出来（该文件触到 450 行硬上限，
`tests/tooling/test_python_source_limits.py`）：这里只放"取行面"，
`db.py` 保留连接工厂、schema 与 `SerializedConnection`。
两个类 **都** 从 `db.py` 重新导出，既有 import 路径不变。

口径（两个类共用）：**读语句的行在锁内取尽**——只锁语句是不够的，
调用方的取行可能落在锁外，被别的线程的语句/提交打断（实测：写后立读
有 10~20/96 读不到，甚至拿回列数不对的行；`conn.cursor()` 自建游标
还会退回 cycle 8 的崩溃类）。

本模块只使用标准库 sqlite3，不引入未 pin 依赖。
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator
from typing import Any, cast


class MaterializedRows:
    """只读游标视图：行已在锁内取尽，之后取行不再触碰连接。

    为什么需要它：`execute()` 与调用方的取行之间是一个窗口，共享连接上
    别的线程可以在这段时间里执行语句或提交，使这次取行拿到**不属于本语句**的结果
    （实测：读不到刚提交的行，甚至拿回列数不对的行）。把行在锁内取尽后，
    取行不再依赖连接状态。

    覆盖的是本仓实际用到的游标面（`fetchone` / `fetchmany` / `fetchall` / 迭代 /
    `rowcount` / `description` / `close`）；它不是 `sqlite3.Cursor`。
    `conn.cursor()` 自建游标走 `SerializedCursor`（同一套锁内执行 + 锁内取尽口径）。
    """

    __slots__ = ("_rows", "_offset", "description", "rowcount", "lastrowid")

    def __init__(self, source: sqlite3.Cursor, rows: list[Any]) -> None:
        self._rows = rows
        self._offset = 0
        self.description = source.description
        self.rowcount = source.rowcount
        self.lastrowid = source.lastrowid

    def fetchone(self) -> Any:
        if self._offset >= len(self._rows):
            return None
        row = self._rows[self._offset]
        self._offset += 1
        return row

    def fetchmany(self, size: int = 1) -> list[Any]:
        """默认取 1 行（与默认 `arraysize = 1` 的真游标一致）。"""
        rows = self._rows[self._offset : self._offset + size]
        self._offset += len(rows)
        return rows

    def fetchall(self) -> list[Any]:
        rows = self._rows[self._offset :]
        self._offset = len(self._rows)
        return rows

    def __iter__(self) -> Iterator[Any]:
        while self._offset < len(self._rows):
            yield self.fetchone()

    def close(self) -> None:
        """真游标的 close 之后不能再取行；物化视图的取行只读本地列表，故为 no-op。"""


class SerializedCursor:
    """`conn.cursor()` 自建游标的收口包装（PLAN-20260915-075）。

    `SerializedConnection` 原本只把 `execute/executemany/executescript` 收进锁，
    `conn.cursor()` 返回的仍是**裸** `sqlite3.Cursor`——它的语句执行不取锁、
    取行也不物化：同一连接上并发使用会退回 cycle 8 的崩溃类（`InterfaceError`）
    与 cycle 9 的读错类。这个包装把自建游标也收进**同一把锁与同一套物化口径**：

        语句在锁内执行（`execute` / `executemany` / `executescript`）；
        读语句的行在锁内取尽，之后的 `fetch*` 只读本地列表。

    为什么"取尽"是必须的（实测，同一脚本、同参数）：裸游标上先执行一条读语句、
    再取行，若中间同连接上发生写入 + 提交，取回的结果里会**多出**那行新数据
    （读跨越了提交点）；并发下还会出现列数不对的行。锁内取尽后，
    这次读的结果在语句执行时刻就定死。

    它不是 `sqlite3.Cursor`：覆盖本仓实际用到的游标面（`execute` / `executemany` /
    `executescript` / `fetchone` / `fetchmany` / `fetchall` / 迭代 / `close` /
    `description` / `rowcount` / `lastrowid` / `arraysize` / `connection`）。
    """

    __slots__ = ("_connection", "_lock", "_raw", "_view", "arraysize")

    def __init__(self, connection: sqlite3.Connection, lock: threading.RLock, raw: Any) -> None:
        self._connection = connection
        self._lock = lock
        self._raw = raw
        self._view: MaterializedRows | None = None
        self.arraysize = 1

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    @property
    def description(self) -> Any:
        return self._raw.description

    @property
    def rowcount(self) -> int:
        return cast(int, self._raw.rowcount)

    @property
    def lastrowid(self) -> int | None:
        return cast("int | None", self._raw.lastrowid)

    def _forward(self, method: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
        """转发到裸游标（与 SerializedConnection 同形：不拼装、不解析、不缓存语句文本）。"""
        return getattr(self._raw, method)(*args, **kwargs)

    def _statement(self, *args: Any, **kwargs: Any) -> SerializedCursor:
        with self._lock:
            self._forward("execute", args, kwargs)
            self._take_rows()
        return self

    def _many_statements(self, *args: Any, **kwargs: Any) -> SerializedCursor:
        with self._lock:
            self._forward("executemany", args, kwargs)
            self._view = None
        return self

    def _script(self, *args: Any, **kwargs: Any) -> SerializedCursor:
        with self._lock:
            self._forward("executescript", args, kwargs)
            self._view = None
        return self

    execute = _statement
    executemany = _many_statements
    executescript = _script

    def _take_rows(self) -> None:
        """锁内取尽（调用方必须已持锁）；写语句没有结果集，视图置空。"""
        if self._raw.description is None:
            self._view = None
            return
        self._view = MaterializedRows(self._raw, list(self._raw.fetchall()))

    def fetchone(self) -> Any:
        return self._view.fetchone() if self._view is not None else self._raw.fetchone()

    def fetchmany(self, size: int | None = None) -> list[Any]:
        """不带 size 时用 `arraysize`（与真游标一致）。"""
        width = self.arraysize if size is None else size
        source = self._view if self._view is not None else self._raw
        return cast("list[Any]", source.fetchmany(width))

    def fetchall(self) -> list[Any]:
        source = self._view if self._view is not None else self._raw
        return cast("list[Any]", source.fetchall())

    def __iter__(self) -> Iterator[Any]:
        return iter(self._view if self._view is not None else self._raw)

    def close(self) -> None:
        with self._lock:
            self._raw.close()
            self._view = None
