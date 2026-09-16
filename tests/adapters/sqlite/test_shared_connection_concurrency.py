"""共享 SQLite 连接的并发写回归测试（PLAN-20260915-070 / RECHECK-069 W-1）。

背景：控制面把**同一个连接对象**注入多个 store，而 FastAPI 的同步端点跑在 threadpool 里、
调度守护线程也在写。`check_same_thread=False` 只关掉了"只能在创建线程里用"的检查，
两个线程同时对一条连接执行语句会破坏 sqlite3 的内部状态：

    sqlite3.InterfaceError: bad parameter or other API misuse

实测（live 控制面，12 线程 24 个 `POST /ops/schedules`）：
修复前 **19×201 / 2×500 / 2×404 / 1×409**；加锁后 **23×201 / 1×404 / 0×500**。

本文件钉住的是**这一类**：并发语句不再抛 `InterfaceError`，且所有写入最终都落库。
**不钉**（也**不宣称**）"写后立读一定看得见"——那需要每线程连接或显式事务，
本轮未做（见 RECHECK-070 的告警与下一轮条目）。
"""

from __future__ import annotations

import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from adapters.sqlite.db import BUSY_TIMEOUT_MS, connect
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
        note="concurrency probe",
    )


def _write_rounds(store: SqliteScheduleStore, index: int) -> None:
    """一个 worker 的所有往返：反复写（每条都是一个完整语句 + commit）。"""
    for round_index in range(ROUNDS):
        store.save_definition(_definition(f"concurrency_probe_{index}_{round_index}"))


def test_concurrent_writers_on_one_connection_do_not_break_it(tmp_path: Path) -> None:
    """修复前：并发执行会抛 `sqlite3.InterfaceError`；修复后：无异常且写入全部落库。"""
    store = SqliteScheduleStore(tmp_path.joinpath("control.db"))
    try:
        with ThreadPoolExecutor(max_workers=THREADS) as pool:
            # 任一 worker 抛异常都会在这里浮出来（这正是修复前的情形）
            list(pool.map(lambda index: _write_rounds(store, index), range(THREADS)))

        stored = {item.name for item in store.list_definitions()}
        expected = {
            f"concurrency_probe_{index}_{round_index}"
            for index in range(THREADS)
            for round_index in range(ROUNDS)
        }
        assert expected <= stored, f"缺失 {len(expected - stored)} 行"
    finally:
        store.close()


def test_connect_serializes_statements_and_sets_a_busy_timeout(tmp_path: Path) -> None:
    connection = connect(tmp_path.joinpath("pragmas.db"))
    try:
        assert isinstance(connection, sqlite3.Connection)
        assert type(connection).__name__ == "SerializedConnection"
        assert connection.execute("PRAGMA busy_timeout").fetchone()[0] == BUSY_TIMEOUT_MS

        errors: list[str] = []

        def hammer() -> None:
            try:
                for _ in range(50):
                    connection.execute("SELECT 1").fetchall()
            except BaseException as exc:  # noqa: BLE001 - 用例要把异常原样带出来
                errors.append(repr(exc))

        threads = [threading.Thread(target=hammer) for _ in range(THREADS)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert errors == []
    finally:
        connection.close()
