"""共享连接上的**读原子性**回归（PLAN-20260915-071 / RECHECK-070 W-1）。

cycle 8 把语句收进一把锁之后，还剩一类**静默错误**：共享连接上，`execute()` 拿到的
游标在取行之前会被另一个线程的语句/提交打断，于是"写后立读"读不到刚提交的行，
甚至拿回**列数不对**的行。实测（12 线程 × 8 轮"写后立读"，同一脚本同参数）：

    语句级串行（cycle 8 的形态）：miss 10 / 14 / 13 / 16 / 20 / 6 / 15 / 11（每轮 96 次读）
    读在锁内取尽（本轮修法）    ：miss 0 / 0 / 0

**反证的可移植性（cycle 9 的 CI 教训）**：这是**真实竞态**，复现率随并行度变化——
8+ 核 Windows 上每次都能压出 10~20/96，2 vCPU 的 CI runner 上 12 线程 × 8 轮 × 3 次
**一次都没复现**（run 35115260874 的 ubuntu job 就是被这条判红）。
把确定性做法也试过了（拿着游标不放、让另一线程写+提交后再取行）：**不触发**——
竞态需要两个线程**同时**在 sqlite3 C 调用里（GIL 已释放），不是简单的时间窗交错。
因此这里把门禁换成**结构判据**（确定性、任何机器都成立）：

    产品路径：返回行的语句在**锁内取尽**（`MaterializedRows`）
    退回语句级串行：返回裸 `sqlite3.Cursor`（取行在锁外 ⇒ 不存在原子性）

负载型复现器仍留在记录里（RECHECK-071 的实测数字与脚本），只是不再当 CI 门禁。

本文件钉住四件事：

1. 共享连接上写后立读**不再对不上真相**（负载型，只断言"无坏结果"）；
2. **反证**：结构判据——退回语句级串行时，读结果不再在锁内取尽；
3. 物化视图与真游标在**仓库实际用到的游标面**上行为一致；
4. 并发下逐行解码不再出现"行列数不对"（`zip(..., strict=True)` 的那类崩溃）。
"""

from __future__ import annotations

import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, cast

from adapters.sqlite.db import SerializedConnection, connect
from adapters.sqlite.schedule_store import SqliteScheduleStore
from packages.domain.schedules import ScheduleDefinition, ScheduleJob

THREADS = 12
ROUNDS = 8


def _definition(name: str) -> ScheduleDefinition:
    return ScheduleDefinition(
        name=name,
        job=ScheduleJob.RETENTION,
        interval_seconds=30.0,
        enabled=True,
        builtin=False,
        note="read atomicity probe",
    )


def _run_round_trips(store: SqliteScheduleStore) -> list[str]:
    """12 线程 × 8 轮"写一条、立刻读同一条"，返回**对不上真相**的每一处描述。

    对不上有两种形态，都算问题：读不到刚写的行（miss），或者读回来的行**不是那条**
    （列数不对 ⇒ `_decode` 的 `zip(..., strict=True)` 直接抛）。
    """
    problems: list[str] = []
    lock = threading.Lock()

    def worker(index: int) -> None:
        for round_index in range(ROUNDS):
            name = f"atomic_probe_{index}_{round_index}"
            problem = ""
            try:
                store.save_definition(_definition(name))
                if store.get_definition(name) is None:
                    problem = "read miss"
            except Exception as exc:  # noqa: BLE001 - 坏结果是证据，不是用例错误
                problem = repr(exc)
            if problem:
                with lock:
                    problems.append(f"{name}: {problem}")

    with ThreadPoolExecutor(max_workers=THREADS) as pool:
        list(pool.map(worker, range(THREADS)))
    return problems


def test_write_then_read_on_a_shared_connection_sees_the_row(tmp_path: Path) -> None:
    """AC-01：读在锁内取尽后，"写后立读"0 miss（修复前 10~20/96）。"""
    store = SqliteScheduleStore(tmp_path.joinpath("control.db"))
    try:
        problems = [_run_round_trips(store) for _ in range(3)]
    finally:
        store.close()

    assert problems == [[], [], []], f"共享连接上仍读到对不上真相的结果：{problems}"


class _StatementOnly(SerializedConnection):
    """cycle 8 的形态：语句级串行，但**不**把行在锁内取尽（取行回到调用方手里）。"""

    def _statement_only(self, *args: Any, **kwargs: Any) -> sqlite3.Cursor:
        return cast(sqlite3.Cursor, self._under_lock("execute", args, kwargs))

    execute = _statement_only


def _statement_only_store(db_path: Path) -> SqliteScheduleStore:
    connection = sqlite3.connect(str(db_path), check_same_thread=False, factory=_StatementOnly)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA busy_timeout=5000")
    return SqliteScheduleStore(db_path, connection=connection)


def test_statement_level_serialization_does_not_take_rows_inside_the_lock(tmp_path: Path) -> None:
    """AC-02 反证（**结构判据**，确定性）：退回语句级串行时，读结果不再锁内取尽。

    症状级（负载压出读错）在 2 vCPU 的 CI runner 上复现不出来（见模块 docstring），
    因此门禁改判**结构**：产品连接返回 `MaterializedRows`（行已在锁内取尽），
    退回形态返回裸 `sqlite3.Cursor`（行还在连接上，取行在锁外）。谁把物化改回去，
    这条就红。
    """
    product = connect(tmp_path.joinpath("product.db"))
    product_store = SqliteScheduleStore(tmp_path.joinpath("product.db"), connection=product)
    statement_only = _statement_only_store(tmp_path.joinpath("raw.db"))
    try:
        for index in range(3):
            product_store.save_definition(_definition(f"atomic_{index}"))
            statement_only.save_definition(_definition(f"atomic_{index}"))

        product_cursor = product.execute("SELECT name FROM schedules ORDER BY name")
        assert type(product_cursor).__name__ == "MaterializedRows"
        # 行已在锁内取尽：之后的写入不改变这次读的结果
        product_store.save_definition(_definition("later"))
        expected = [("atomic_0",), ("atomic_1",), ("atomic_2",)]
        assert [tuple(row) for row in product_cursor] == expected

        raw_cursor = statement_only._conn.execute(  # noqa: SLF001 - 反证要看连接的真实形态
            "SELECT name FROM schedules ORDER BY name"
        )
        assert isinstance(raw_cursor, sqlite3.Cursor)
        assert type(raw_cursor).__name__ != "MaterializedRows"
    finally:
        product.close()
        product_store.close()
        statement_only.close()


def _seed(connection: sqlite3.Connection) -> None:
    connection.executescript(
        "CREATE TABLE IF NOT EXISTS parity (name TEXT PRIMARY KEY, n INTEGER NOT NULL);"
    )
    connection.executemany(
        "INSERT INTO parity (name, n) VALUES (?, ?)", [("a", 1), ("b", 2), ("c", 3)]
    )
    connection.commit()


def _surface(connection: sqlite3.Connection) -> dict[str, Any]:
    """仓库实际用到的游标面：fetchone / 迭代 / fetchall / fetchmany / rowcount / description。"""
    cursor = connection.execute("SELECT name, n FROM parity ORDER BY name")
    first = cursor.fetchone()
    remainder = [tuple(row) for row in cursor]
    exhausted = cursor.fetchall()
    description = cursor.description
    cursor.close()

    many = connection.execute("SELECT name, n FROM parity ORDER BY name").fetchmany(2)
    empty = connection.execute("SELECT name FROM parity WHERE name = ?", ("zzz",))
    updated = connection.execute("UPDATE parity SET n = n + 1 WHERE name = ?", ("a",))
    return {
        "first": tuple(first) if first is not None else None,
        "remainder": remainder,
        "exhausted": exhausted,
        "description": description,
        "many": [tuple(row) for row in many],
        "empty_rowcount": empty.rowcount,
        "update_rowcount": updated.rowcount,
    }


def test_materialized_view_matches_a_real_cursor(tmp_path: Path) -> None:
    """AC-03：同一 SQL、同一数据下，物化视图与真游标的可观测行为逐项一致。"""
    plain = sqlite3.connect(":memory:")
    wrapped = connect(tmp_path.joinpath("parity.db"))
    try:
        _seed(plain)
        _seed(wrapped)
        assert _surface(wrapped) == _surface(plain)
    finally:
        plain.close()
        wrapped.close()


def test_concurrent_reads_never_decode_a_short_row(tmp_path: Path) -> None:
    """AC-04：并发读写时 `list_definitions()` 逐行解码不再抛"行列数不对"。"""
    store = SqliteScheduleStore(tmp_path.joinpath("decode.db"))
    failures: list[str] = []

    def reader() -> None:
        for _ in range(20):
            try:
                store.list_definitions()
            except BaseException as exc:  # noqa: BLE001 - 用例要把异常原样带出来
                failures.append(repr(exc))

    def writer(index: int) -> None:
        for round_index in range(ROUNDS):
            store.save_definition(_definition(f"decode_probe_{index}_{round_index}"))

    try:
        with ThreadPoolExecutor(max_workers=THREADS) as pool:
            readers = [pool.submit(reader) for _ in range(4)]
            writers = [pool.submit(writer, index) for index in range(8)]
            for future in readers + writers:
                future.result()
        stored = {item.name for item in store.list_definitions()}
    finally:
        store.close()

    assert failures == []
    assert len(stored) == 8 * ROUNDS
