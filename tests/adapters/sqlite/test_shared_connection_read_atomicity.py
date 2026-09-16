"""共享连接上的**读原子性**回归（PLAN-20260915-071 / RECHECK-070 W-1）。

cycle 8 把语句收进一把锁之后，还剩一类**静默错误**：共享连接上，`execute()` 拿到的
游标在取行之前会被另一个线程的语句/提交打断，于是"写后立读"读不到刚提交的行，
甚至拿回**列数不对**的行。实测（12 线程 × 8 轮"写后立读"，同一脚本同参数）：

    语句级串行（cycle 8 的形态）：miss 10 / 14 / 13 / 16 / 20 / 6 / 15 / 11（每轮 96 次读）
    读在锁内取尽（本轮修法）    ：miss 0 / 0 / 0

本文件钉住四件事：

1. 共享连接上写后立读**不再 miss**（修复前会红）；
2. **反证**：同一负载打在"语句级串行、不取尽行"的连接上**仍会 miss**
   —— 证明第 1 条测的是这件事，而不是别的东西；
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
    """cycle 8 的形态：语句级串行，但**不**把行在锁内取尽。

    用来做反证——如果这个形态也 0 miss，说明本文件的用例没测到真问题。
    """

    def _statement_only(self, *args: Any, **kwargs: Any) -> sqlite3.Cursor:
        return cast(sqlite3.Cursor, self._under_lock("execute", args, kwargs))

    execute = _statement_only


def _statement_only_store(db_path: Path) -> SqliteScheduleStore:
    connection = sqlite3.connect(str(db_path), check_same_thread=False, factory=_StatementOnly)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA busy_timeout=5000")
    return SqliteScheduleStore(db_path, connection=connection)


def test_statement_level_serialization_still_misses_the_row(tmp_path: Path) -> None:
    """AC-02 反证：语句级串行的连接上，同一负载**必须**还能复现对不上的读。

    若某天这条不再成立（例如 CPython 的 sqlite3 并发语义变了），说明本文件
    依赖的前提变了：那时要重做取证并改写本文件的口径，而不是把它删掉。
    """
    observed: list[list[str]] = []
    for attempt in range(3):
        store = _statement_only_store(tmp_path.joinpath(f"statement_only_{attempt}.db"))
        try:
            observed.append(_run_round_trips(store))
        finally:
            store.close()

    assert any(problems for problems in observed), (
        f"语句级串行的形态没有复现出对不上的读，本文件的第一条用例失去反证：{observed}"
    )


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
