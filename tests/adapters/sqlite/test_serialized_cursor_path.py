"""`conn.cursor()` 自建游标的收口回归（PLAN-20260915-075 / RECHECK-074 后继）。

`SerializedConnection` 此前只把 `execute/executemany/executescript` 收进锁：
`conn.cursor()` 返回的仍是**裸** `sqlite3.Cursor`，它的语句执行不取锁、取行也不物化，
于是"这条连接上的语句是串行的、读是原子的"这句承诺只对**一个入口**成立
（模块 docstring 也如实写着这个缺口）。本文件钉住缺口已经补上：

1. **结构**：`conn.cursor()` 返回 `SerializedCursor`，其 `execute()` 的结果是
   **锁内取尽**的物化视图（与 `conn.execute()` 同一套口径）；
2. **锁真的被取**（确定性，不依赖负载）：主线程持有连接锁时，另一线程通过自建游标
   执行语句会**阻塞**，释放后立刻完成；
3. **读的结果在 execute 时刻定死**（确定性）：execute 之后、取行之前发生同连接
   写入 + 提交，取回的行**不含**那行新数据；取行也不再依赖连接后续状态
   （关门之后仍可取）；
4. **读写往返与游标面**：自建游标写入/批量写入/关闭，物化视图与真游标的取行面一致。

**为什么反证选"关门之后取行"而不是"读到了提交之后的新行"**（实测记录，探针见
`scratch/goal3-cycle12-probe{3,4,5}-*.py`，SQLite 3.50.4 / win32）：

```text
裸游标：读语句 execute → 同连接写入 + 提交 → 再取行
    带主键 + 按列排序   ：三行都在（新行进来了）
    带主键、不排序      ：三行都在
    无主键 + 按列排序   ：只有两行（sorter 在首次 step 就定死结果集）
    无主键、不排序      ：三行都在
```

也就是说"裸游标会不会读到提交之后的新行"**取决于查询计划**（流式扫描 vs 排序物化），
把它写成断言就是不可移植的判据（MEM-048 的教训）。所以这里取一条与计划无关的
对比：裸游标取行**要碰连接**（关门即 `ProgrammingError`），锁内取尽后取行只读本地列表。
"""

from __future__ import annotations

import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from pathlib import Path
from typing import Any, cast

import pytest

from adapters.sqlite.db import (
    MaterializedRows,
    SerializedConnection,
    SerializedCursor,
    connect,
)


def _plain(rows: list[Any]) -> list[tuple[Any, ...]]:
    """`connect()` 的 row_factory 是 `sqlite3.Row`，断言用普通元组更好读。"""
    return [tuple(row) for row in rows]


def _connection(tmp_path: Path, name: str) -> SerializedConnection:
    return cast(SerializedConnection, connect(tmp_path.joinpath(f"{name}.db")))


def _seed(connection: sqlite3.Connection) -> None:
    connection.execute("CREATE TABLE IF NOT EXISTS parity (name TEXT, n INTEGER)")
    connection.executemany(
        "INSERT INTO parity (name, n) VALUES (?, ?)",
        [("a", 1), ("b", 2)],
    )
    connection.commit()


def test_self_made_cursor_is_a_serialized_cursor_that_materializes(tmp_path: Path) -> None:
    """AC-01：自建游标不是裸游标；它的读语句结果在锁内取尽。"""
    connection = _connection(tmp_path, "structure")
    try:
        cursor = connection.cursor()
        assert isinstance(cursor, SerializedCursor)
        assert not isinstance(cursor, sqlite3.Cursor)

        connection.execute("CREATE TABLE IF NOT EXISTS parity (name TEXT, n INTEGER)")
        connection.commit()
        result = cursor.execute("SELECT name, n FROM parity ORDER BY name")
        # 与 conn.execute() 同一口径：读结果已物化（不再依赖连接后续状态）
        assert result is cursor
        raw_cursor = cast(Any, cursor)
        assert type(raw_cursor._view).__name__ == "MaterializedRows"
        assert isinstance(raw_cursor._view, MaterializedRows)
        assert cursor.fetchall() == []
    finally:
        connection.close()


def test_self_made_cursor_statement_waits_for_the_connection_lock(tmp_path: Path) -> None:
    """AC-02：锁真的被取——持有锁时另一线程的语句会阻塞，释放后完成（确定性）。"""
    connection = _connection(tmp_path, "lock")
    connection.execute("CREATE TABLE IF NOT EXISTS parity (name TEXT, n INTEGER)")
    connection.executemany(
        "INSERT INTO parity (name, n) VALUES (?, ?)",
        [("a", 1), ("b", 2)],
    )
    connection.commit()
    entered = threading.Event()
    release = threading.Event()

    def hold_the_lock() -> None:
        with connection._lock:  # noqa: SLF001 - 本用例测的就是这把锁
            entered.set()
            assert release.wait(10)

    def run_statement() -> list[Any]:
        cursor = connection.cursor()
        cursor.execute("SELECT n FROM parity ORDER BY n")
        # `cursor()` 在类型上放宽成 Any（sqlite3 的 cursor 是重载），这里显式收回类型
        return cast("list[Any]", cursor.fetchall())

    holder = threading.Thread(target=hold_the_lock)
    holder.start()
    try:
        assert entered.wait(10)
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(run_statement)
            with pytest.raises(FutureTimeout):
                pending.result(timeout=0.5)  # 锁在别人手里 ⇒ 语句进不去
            release.set()
            assert _plain(pending.result(timeout=10)) == [(1,), (2,)]
    finally:
        release.set()
        holder.join(timeout=10)
        connection.close()


def test_self_made_cursor_freezes_rows_at_execute_time(tmp_path: Path) -> None:
    """AC-03：execute 之后、取行之前发生的写入 + 提交**不会**进入这次读的结果。

    表形态刻意取"带主键 + 按列排序"——这正是实测里裸游标会把新行读进来的那种形态
    （见文件头实测记录），因此本条与裸游标的行为**可区分**，不是自证。
    """
    connection = _connection(tmp_path, "frozen")
    connection.execute(
        "CREATE TABLE IF NOT EXISTS parity (name TEXT PRIMARY KEY, n INTEGER NOT NULL)"
    )
    connection.executemany("INSERT INTO parity (name, n) VALUES (?, ?)", [("a", 1), ("b", 2)])
    connection.commit()
    try:
        reader = connection.cursor()
        reader.execute("SELECT name, n FROM parity ORDER BY name")

        writer = connection.cursor()
        writer.execute("INSERT INTO parity (name, n) VALUES ('c', 3)")
        connection.commit()

        assert _plain(reader.fetchall()) == [("a", 1), ("b", 2)]
    finally:
        connection.close()


def test_self_made_cursor_rows_survive_the_connection(tmp_path: Path) -> None:
    """AC-03：取行只读本地列表——连接关掉之后仍然取得到（与裸游标正相反）。"""
    connection = _connection(tmp_path, "survive")
    _seed(connection)
    cursor = connection.cursor()
    cursor.execute("SELECT name, n FROM parity ORDER BY name")
    connection.close()

    assert _plain(cursor.fetchall()) == [("a", 1), ("b", 2)]


def test_a_raw_cursor_fetch_depends_on_the_going_connection(tmp_path: Path) -> None:
    """AC-03 反证（与查询计划无关）：**裸**游标取行要碰连接，关门即失败。

    这条之所以能当反证：它不依赖查询计划，也不依赖负载（对比文件头那组"取决于
    sorter 还是流式扫描"的实测）。裸游标关门后取行抛 `ProgrammingError`；
    `SerializedCursor` 在锁内取尽，同样的动作只是读本地列表（见上一条用例）。
    """
    connection = sqlite3.connect(str(tmp_path.joinpath("raw.db")))
    _seed(connection)
    reader = connection.cursor()
    reader.execute("SELECT name, n FROM parity ORDER BY name")
    connection.close()

    with pytest.raises(sqlite3.ProgrammingError):
        reader.fetchall()


def test_a_raw_cursor_stops_being_materialized_or_locked(tmp_path: Path) -> None:
    """AC-03 结构补充：裸连接上的游标**没有**物化视图，自建游标有。

    这不是行为判据的替代，而是把"两个入口的形态差异"写成结构事实：
    裸游标（`sqlite3.Cursor`）连 `_view` 属性都没有，自建游标有且非空。
    """
    raw_connection = sqlite3.connect(str(tmp_path.joinpath("raw_shape.db")))
    _seed(raw_connection)
    try:
        raw_reader = raw_connection.cursor()
        raw_reader.execute("SELECT name, n FROM parity ORDER BY name")
        assert not hasattr(raw_reader, "_view")
    finally:
        raw_connection.close()

    connection = _connection(tmp_path, "wrapped_shape")
    _seed(connection)
    try:
        wrapped = connection.cursor()
        wrapped.execute("SELECT name, n FROM parity ORDER BY name")
        assert isinstance(cast(Any, wrapped)._view, MaterializedRows)
    finally:
        connection.close()


def test_self_made_cursor_round_trips_writes_and_reads(tmp_path: Path) -> None:
    """AC-04：写（单条/批量）经自建游标落库，提交后读得回来；rowcount 如实。"""
    connection = _connection(tmp_path, "roundtrip")
    try:
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS parity (name TEXT, n INTEGER)")
        cursor.executemany(
            "INSERT INTO parity (name, n) VALUES (?, ?)",
            [("a", 1), ("b", 2), ("c", 3)],
        )
        assert cursor.rowcount == 3
        connection.commit()
        # lastrowid 只由单条 execute 更新（executemany 不更新）——真游标同样如此
        cursor.execute("INSERT INTO parity (name, n) VALUES ('d', 4)")
        assert cursor.lastrowid == 4

        assert _plain(cursor.execute("SELECT COUNT(*) FROM parity").fetchall()) == [(4,)]
        assert _plain(cursor.execute("SELECT name FROM parity ORDER BY name").fetchall()) == [
            ("a",),
            ("b",),
            ("c",),
            ("d",),
        ]
    finally:
        connection.close()


def test_self_made_cursor_covers_the_cursor_surface_the_repo_uses(tmp_path: Path) -> None:
    """AC-04：物化视图的取行面（fetchone / fetchmany / 迭代 / arraysize）与真游标一致。"""
    connection = _connection(tmp_path, "surface")
    _seed(connection)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT name, n FROM parity ORDER BY name")
        assert tuple(cursor.fetchone()) == ("a", 1)
        assert _plain(cursor.fetchmany(1)) == [("b", 2)]
        assert cursor.fetchall() == []

        listing = connection.cursor()
        listing.execute("SELECT name FROM parity ORDER BY name")
        listing.arraysize = 2
        assert _plain(listing.fetchmany()) == [("a",), ("b",)]
        assert listing.fetchone() is None

        iterated = connection.cursor()
        iterated.execute("SELECT n FROM parity ORDER BY n")
        assert [row[0] for row in iterated] == [1, 2]
        assert iterated.description is not None
        assert iterated.connection is connection

        cursor.close()
        with pytest.raises(sqlite3.ProgrammingError):
            cursor.fetchone()
    finally:
        connection.close()


def test_self_made_cursor_keeps_writes_serialized_under_load(tmp_path: Path) -> None:
    """AC-05：并发写经自建游标不再崩（回归，不是反证——反证见上面两条确定性用例）。

    负载型复现不可移植（见 MEM-048）：本用例是**回归**，证明修复后并发使用不再出现
    `InterfaceError`；不把它当成"修复前必然失败"的证明。
    """
    connection = _connection(tmp_path, "load")
    connection.execute("CREATE TABLE IF NOT EXISTS parity (name TEXT, n INTEGER)")
    connection.commit()
    problems: list[str] = []

    def worker(index: int) -> None:
        try:
            for round_index in range(8):
                label = f"w{index}-{round_index}"
                cursor = connection.cursor()
                cursor.execute("INSERT INTO parity (name, n) VALUES (?, ?)", (label, index))
                connection.commit()
                reader = connection.cursor()
                reader.execute("SELECT COUNT(*) FROM parity WHERE name = ?", (label,))
                rows = _plain(reader.fetchall())
                if rows != [(1,)]:
                    problems.append(f"{index}/{round_index}: {rows}")
        except Exception as exc:  # noqa: BLE001 - 任何异常都算这次收口没做到
            problems.append(f"{index}: {type(exc).__name__}: {exc}")

    try:
        threads = [threading.Thread(target=worker, args=(index,)) for index in range(12)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=60)
        assert problems == []
        assert _plain(connection.execute("SELECT COUNT(*) FROM parity").fetchall()) == [(96,)]
    finally:
        connection.close()
