"""每线程连接的锁粒度（GOAL-004 cycle 5 = EC-05）。

判据（文件库）：

1. **真的每线程一条**：两个线程各自拿到**不同**的连接对象（共享连接不再被跨线程使用）；
2. **线程内写后立读**：本线程提交的写在同一条连接上立刻可见（`SerializedConnection`
   时代靠同一把锁，现在靠"连接属于线程"）；
3. **跨线程写可见**：A 提交后 B 读到（WAL + 即时提交，不需要同一把大锁）；
4. **并发写不掉行、不抛 `InterfaceError`**：12 线程 × 8 次写全部落库；
5. **关闭是"关全部"**：`close_all()` 关闭登记过的每条连接（应用 shutdown 路径）；
6. **`:memory:` 边界**：内存库属于连接 ⇒ 这种路径**共用一条**（显式钉住，不是退化成
   每线程空库）。
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from adapters.sqlite.db import SCHEMA_SQL
from adapters.sqlite.pool import ThreadLocalConnection, is_memory_path

THREADS = 12
ROUNDS = 8


def _pool(tmp_path: Path, name: str = "control.db") -> ThreadLocalConnection:
    pool = ThreadLocalConnection(tmp_path / name)
    pool.executescript(SCHEMA_SQL)
    return pool


def _insert_task(pool: ThreadLocalConnection, task_id: str) -> None:
    """写一行 task（语句字面量就地写：不经过模块级常量/参数拼装）。"""
    with pool:
        pool.execute(
            "INSERT INTO tasks (task_id, run_id, attempt, status, task_json, contract_json,"
            " created_at) VALUES (?, 'run-pool', 1, 'QUEUED', '{}', '{}', '2026-01-01T00:00:00Z')",
            (task_id,),
        )


def _task_ids(pool: ThreadLocalConnection) -> list[str]:
    rows = pool.execute("SELECT task_id FROM tasks ORDER BY task_id").fetchall()
    return [row[0] for row in rows]


def test_a_file_backed_control_plane_gets_one_connection_per_thread(tmp_path: Path) -> None:
    """AC-01：同一把句柄在两个线程上拿到两条不同连接（跨线程共用到此为止）。"""
    pool = _pool(tmp_path)  # 主线程自己已经用过一次（建表）⇒ 基线 1 条
    baseline = pool.connection_count()
    seen: dict[str, int] = {}
    ready = threading.Barrier(2)

    def record(name: str) -> None:
        ready.wait()
        seen[name] = id(pool.current())

    threads = [threading.Thread(target=record, args=(f"t{index}",)) for index in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert len(set(seen.values())) == 2, f"每线程必须有自己的连接：{seen}"
    assert pool.connection_count() == baseline + 2, "每条线程各开一条（懒创建），不多开"


def test_writes_are_visible_inside_the_thread_and_across_threads(tmp_path: Path) -> None:
    """AC-02/03：线程内写后立读；跨线程提交后可见（WAL 语义，不靠一把大锁）。"""
    pool = _pool(tmp_path)
    writer_done = threading.Event()

    def writer() -> None:
        _insert_task(pool, "a1")
        assert _task_ids(pool) == ["a1"], "本线程提交的写必须立刻可见"
        writer_done.set()

    reader_seen: list[list[str]] = []

    def reader() -> None:
        assert writer_done.wait(10)
        reader_seen.append(_task_ids(pool))

    writer_thread = threading.Thread(target=writer)
    reader_thread = threading.Thread(target=reader)
    writer_thread.start()
    reader_thread.start()
    writer_thread.join(timeout=10)
    reader_thread.join(timeout=10)

    assert reader_seen == [["a1"]], "另一线程提交的写必须可见（连接之间靠 WAL 协调）"


def test_twelve_threads_write_without_lost_rows_or_interface_errors(tmp_path: Path) -> None:
    """AC-04：12 线程 × 8 次写全部落库，且不抛 `InterfaceError`（并发写回归的池版）。"""
    pool = _pool(tmp_path)
    errors: list[BaseException] = []
    errors_lock = threading.Lock()

    def worker(thread_index: int) -> None:
        try:
            for round_index in range(ROUNDS):
                _insert_task(pool, f"t{thread_index:02d}-{round_index:02d}")
        except BaseException as exc:  # noqa: BLE001 - 并发缺陷要原样带回主线程
            with errors_lock:
                errors.append(exc)

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        list(executor.map(worker, range(THREADS)))

    assert errors == [], f"并发写不得抛异常：{errors!r}"
    assert len(_task_ids(pool)) == THREADS * ROUNDS, "每个线程的每次写都必须落库"


def test_close_all_closes_every_registered_connection(tmp_path: Path) -> None:
    """AC-05：`close_all()` 关掉登记过的全部连接（shutdown 不能只关调用线程那条）。"""
    pool = _pool(tmp_path)
    barrier = threading.Barrier(2)

    def touch() -> None:
        barrier.wait()
        pool.execute("SELECT 1").fetchall()

    threads = [threading.Thread(target=touch) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    registered = pool.connection_count()
    assert registered >= 3, "主线程 + 两条工作线程各一条"
    assert pool.close_all() == registered, "关闭必须覆盖登记过的每一条"
    assert pool.close_all() == 0, "重复关闭是幂等的（登记表已清空）"


def test_the_in_memory_path_shares_one_connection_on_purpose(tmp_path: Path) -> None:
    """AC-06：`:memory:` 只能共用一条（内存库属于连接）——显式钉住这个 SQLite 语义。"""
    assert is_memory_path(":memory:") is True
    assert is_memory_path(tmp_path / "control.db") is False

    pool = ThreadLocalConnection(":memory:")
    pool.executescript(SCHEMA_SQL)
    seen: list[int] = []
    barrier = threading.Barrier(2)

    def record() -> None:
        barrier.wait()
        seen.append(id(pool.current()))

    threads = [threading.Thread(target=record) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert len(set(seen)) == 1, "内存库每线程一条会各自看到空库 ⇒ 必须共用"
    assert pool.connection_count() == 1
    pool.close_all()
