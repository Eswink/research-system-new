"""`SerializedConnection` 的**边界枚举**与事务边界收口（PLAN-20260915-076）。

`SerializedConnection` 的承诺是"同一连接的多线程使用串行化（语句 + 事务边界）"。
cycle 8/9/12 分别补上了 `execute` 系列、锁内取尽、自建游标——但"还有哪些入口没收口"
一直是**隐含**的。本文件把它变成**枚举 + 门禁**：

1. `SQLITE_CONNECTION_NAMES` 里逐条记下"刻意不收口"的公共名与理由；
2. 用例断言"未收口集合 == 那张表"——CPython 一旦新增公共方法就会红，
   逼一次"要不要收口"的决定，而不是让它悄悄留在锁外；
3. 事务边界的两个入口（`with conn:` 与 `isolation_level`/`autocommit` 的赋值）
   **已经**收口，用例证明它们确实在锁内（确定性：持锁时另线程阻塞）。

实测背景（PLAN-20260915-076 探针 1）：CPython 3.12 的上下文管理器与属性 setter
在 C 层直接提交/回滚/发语句，**不经过** Python 层的覆写——所以"覆写了 commit 就等于
锁住了事务边界"是错的。
"""

from __future__ import annotations

import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from pathlib import Path
from typing import Any, cast

import pytest

from adapters.sqlite.db import LOCKED_ATTRIBUTES, SerializedConnection, connect

# 刻意不收口的公共名 → 理由。改这张表就是改"边界"，必须写清理由。
NOT_GUARDED = {
    "autocommit": "**赋值**经 __setattr__ 收进锁（见 LOCKED_ATTRIBUTES）；读取只反映标志位。",
    "backup": "整库级操作，本仓不用；要用得先给它定并发语义（它与语句级锁不是一回事）。",
    "blobopen": "BLOB 增量 IO 自己管游标生命周期，本仓不用。",
    "create_aggregate": "注册用户函数（进程级配置，非语句），本仓不用。",
    "create_collation": "同上。",
    "create_function": "同上。",
    "create_window_function": "同上。",
    "deserialize": "整库反序列化，本仓不用。",
    "enable_load_extension": "扩展加载：默认 deny（AGENTS.md §9），本仓不用。",
    "getconfig": "读连接配置（只读）。",
    "getlimit": "读限制值（只读）。",
    "in_transaction": "读事务标志（只读属性）。",
    "interrupt": "**故意不收口**：它的用途就是被别的线程调用以中止正在跑的语句；"
    "把它放进同一把锁会正好废掉这个能力。",
    "isolation_level": "**赋值**经 __setattr__ 收进锁（见 LOCKED_ATTRIBUTES）；读取只读标志位。",
    "iterdump": "整库导出（只读，本仓不用）。",
    "load_extension": "扩展加载：默认 deny，本仓不用。",
    "row_factory": "纯 Python 属性（决定行类型，不触碰连接状态）。",
    "serialize": "整库序列化（只读，本仓不用）。",
    "set_authorizer": "注册授权回调（进程级配置）。",
    "set_progress_handler": "注册进度回调（进程级配置）。",
    "set_trace_callback": "注册追踪回调（进程级配置）；注意它会看到语句文本，属调试面。",
    "setconfig": "改连接配置（本仓不用）。",
    "setlimit": "改限制值（本仓不用）。",
    "text_factory": "纯 Python 属性（决定文本解码，不触碰连接状态）。",
    "total_changes": "读累计改动行数（只读属性）。",
}


def _public_surface() -> set[str]:
    """`sqlite3.Connection` 的公共名（去掉 DB-API 异常槽：那是错误类型，不是连接行为）。"""
    surface: set[str] = set()
    for name in dir(sqlite3.Connection):
        if name.startswith("_"):
            continue
        module_attribute = getattr(sqlite3, name, None)
        if isinstance(module_attribute, type) and issubclass(module_attribute, BaseException):
            continue
        surface.add(name)
    return surface


def _overridden() -> set[str]:
    return {name for name in vars(SerializedConnection) if not name.startswith("_")}


def _connection(tmp_path: Path, name: str) -> SerializedConnection:
    return cast(SerializedConnection, connect(tmp_path.joinpath(f"{name}.db")))


def test_unguarded_surface_matches_the_documented_list() -> None:
    """AC-01：未收口的公共名**恰好**是文档里那张表。

    新增名字（例如换 CPython 版本带来的新方法）⇒ 本用例红 ⇒ 必须做一次决定：
    要么收口，要么在 NOT_GUARDED 里写清为什么不收。
    """
    unguarded = _public_surface() - _overridden() - set(NOT_GUARDED)
    assert unguarded == set(), (
        "出现了既没收口也没登记理由的公共名："
        f"{sorted(unguarded)}；收口它，或在 NOT_GUARDED 里写清理由"
    )
    documented_but_gone = set(NOT_GUARDED) - _public_surface()
    assert documented_but_gone == set(), (
        f"NOT_GUARDED 里有过期的名字（该版本已无此属性）：{sorted(documented_but_gone)}"
    )


def test_locked_attributes_are_a_subset_of_the_documented_surface() -> None:
    """AC-01：`LOCKED_ATTRIBUTES` 必须都在那张表里（两处边界不能各说各话）。"""
    assert LOCKED_ATTRIBUTES <= set(NOT_GUARDED)
    assert LOCKED_ATTRIBUTES <= _public_surface()


def test_context_manager_commits_on_success_and_rolls_back_on_error(tmp_path: Path) -> None:
    """AC-02：`with conn:` 语义与真连接一致——成功提交、异常回滚、不吞异常。"""
    connection = _connection(tmp_path, "ctx")
    connection.execute("CREATE TABLE IF NOT EXISTS ledger (n INTEGER NOT NULL)")
    connection.commit()
    try:
        with connection:
            connection.execute("INSERT INTO ledger (n) VALUES (1)")
        assert connection.execute("SELECT COUNT(*) FROM ledger").fetchone()[0] == 1

        with pytest.raises(RuntimeError):
            with connection:
                connection.execute("INSERT INTO ledger (n) VALUES (2)")
                raise RuntimeError("boom")
        # 异常 ⇒ 回滚：第二行不在
        assert connection.execute("SELECT COUNT(*) FROM ledger").fetchone()[0] == 1
    finally:
        connection.close()


def test_context_manager_holds_the_lock_for_the_whole_block(tmp_path: Path) -> None:
    """AC-03（确定性，PLAN-20260915-077 收紧）：**整块**持锁——块开着时语句进不来。

    PLAN-076 的写法是"另线程持锁、主线程调 `__exit__`"（只测退出那一刻在锁内）。
    PLAN-077 把边界从"语句"提到"操作"后，那种调用方式**不再是合法协议用法**
    （`__exit__` 必须与同线程的 `__enter__` 配对），因此改成更强的一条：
    块开着时，另一个线程的 `execute` 拿不到结果；块退出后立即完成。
    """
    connection = _connection(tmp_path, "ctx_lock")
    in_block = threading.Event()
    release = threading.Event()

    def open_a_block() -> None:
        with connection:
            in_block.set()
            assert release.wait(10)

    holder = threading.Thread(target=open_a_block)
    holder.start()
    try:
        assert in_block.wait(10)
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(lambda: connection.execute("SELECT 1").fetchone())
            with pytest.raises(FutureTimeout):
                pending.result(timeout=0.5)  # 块还开着 ⇒ 语句进不去
            release.set()
            assert pending.result(timeout=10) is not None
    finally:
        release.set()
        holder.join(timeout=10)
        connection.close()


def test_transaction_boundary_attribute_assignment_takes_the_lock(tmp_path: Path) -> None:
    """AC-03（确定性）：`isolation_level` / `autocommit` 的**赋值**在锁内。"""
    connection = _connection(tmp_path, "attr_lock")
    entered = threading.Event()
    release = threading.Event()

    def hold_the_lock() -> None:
        with connection._lock:  # noqa: SLF001 - 本用例测的就是这把锁
            entered.set()
            assert release.wait(10)

    def set_isolation_level() -> None:
        connection.isolation_level = "IMMEDIATE"

    holder = threading.Thread(target=hold_the_lock)
    holder.start()
    try:
        assert entered.wait(10)
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(set_isolation_level)
            with pytest.raises(FutureTimeout):
                pending.result(timeout=0.5)
            release.set()
            pending.result(timeout=10)
        assert connection.isolation_level == "IMMEDIATE"
    finally:
        release.set()
        holder.join(timeout=10)
        connection.close()


def test_reads_of_transaction_flags_do_not_need_the_lock(tmp_path: Path) -> None:
    """AC-03 的对照：读取**不**收口——持锁时读 `isolation_level` 不该阻塞。"""
    connection = _connection(tmp_path, "attr_read")
    entered = threading.Event()
    release = threading.Event()

    def hold_the_lock() -> None:
        with connection._lock:  # noqa: SLF001 - 本用例测的就是这把锁
            entered.set()
            assert release.wait(10)

    holder = threading.Thread(target=hold_the_lock)
    holder.start()
    try:
        assert entered.wait(10)
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(lambda: connection.isolation_level)
            # 默认空串（sqlite3 的 legacy 事务模式）；只读标志位，不进锁也就不阻塞
            assert pending.result(timeout=5) == ""  # type: ignore[comparison-overlap]
            release.set()
    finally:
        release.set()
        holder.join(timeout=10)
        connection.close()


def test_a_statement_execution_and_a_context_exit_do_not_interleave(tmp_path: Path) -> None:
    """AC-04：并发用 `with conn:` 与直接执行语句不会坏（回归，不是反证）。

    负载型用例只作回归（MEM-048）：真正的判据是上面三条确定性用例。
    """
    connection = _connection(tmp_path, "mixed")
    connection.execute("CREATE TABLE IF NOT EXISTS ledger (n INTEGER NOT NULL)")
    connection.commit()
    problems: list[str] = []

    def worker(index: int) -> None:
        try:
            for _ in range(8):
                with connection:
                    connection.execute("INSERT INTO ledger (n) VALUES (?)", (index,))
                # 提交后立刻能读到（读也在锁内取尽）；这里只关心"不抛异常"，
                # 行数断言放到全部线程结束之后（并发下每轮的行数本来就不确定）
                cast(Any, connection.execute("SELECT COUNT(*) FROM ledger")).fetchall()
        except Exception as exc:  # noqa: BLE001 - 任何异常都算这次收口没做到
            problems.append(f"{index}: {type(exc).__name__}: {exc}")

    try:
        threads = [threading.Thread(target=worker, args=(index,)) for index in range(12)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=60)
        assert problems == []
        assert connection.execute("SELECT COUNT(*) FROM ledger").fetchone()[0] == 96
    finally:
        connection.close()
