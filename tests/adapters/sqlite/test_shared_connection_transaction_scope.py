"""GOAL-003 cycle 14：共享连接上的事务边界属于**操作**，不属于连接。

收口前实测（探针 2/3，`scratch/goal3-cycle14-probe*.py`）：

    A. 块内第一个写之后，另一个线程的语句 0.000s 就执行完（块不持锁）
    B. 线程 A 还在块里，线程 B 自己的 `with conn:` 退出就把 A 的半个操作提交了
    C. 线程 B 的块抛错时，回滚把线程 A **已完成**的操作一起抹掉
       （第三个连接看两行全无 = 数据丢失）

本文件的判据都是**确定性**的：不依赖负载、不依赖调度、不依赖查询计划，
用的是"块开着时另线程/外部连接看到什么"的结构对照。
"""

from __future__ import annotations

import ast
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from pathlib import Path

import pytest

from adapters.sqlite.db import SCHEMA_SQL, SerializedConnection, connect

BLOCK_WAIT_SECONDS = 0.5


def _insert_task(connection: sqlite3.Connection, task_id: str) -> None:
    """写一行 task（语句字面量就地写：不经过模块级常量/参数拼装）。"""
    connection.execute(
        "INSERT INTO tasks (task_id, run_id, attempt, status, task_json, contract_json,"
        " created_at) VALUES (?, 'r1', 1, 'QUEUED', '{}', '{}', '2026-01-01T00:00:00Z')",
        (task_id,),
    )


def _shared(tmp_path: Path, name: str) -> SerializedConnection:
    return connect(str(tmp_path / f"{name}.db"))  # type: ignore[return-value]


def _witness(connection: SerializedConnection) -> sqlite3.Connection:
    """第二个连接：只用来"从外面看"共享连接上到底提交了什么。"""
    path = connection.execute("PRAGMA database_list").fetchone()[2]
    return sqlite3.connect(path)


def _count(witness: sqlite3.Connection) -> int:
    return int(witness.execute("SELECT COUNT(*) FROM tasks").fetchone()[0])


def test_a_block_holds_the_lock_for_its_whole_body(tmp_path: Path) -> None:
    """AC-01（确定性）：块开着时，另一个线程的语句 0.5s 内拿不到结果。"""
    connection = _shared(tmp_path, "block_lock")
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
                pending.result(timeout=BLOCK_WAIT_SECONDS)  # 块持有锁 ⇒ 语句进不去
            release.set()
            assert pending.result(timeout=10) is not None
    finally:
        release.set()
        holder.join(timeout=10)
        connection.close()


def test_an_operation_is_all_or_nothing_for_an_outside_witness(tmp_path: Path) -> None:
    """AC-02（确定性）：块内前半段写完、块未退出时，外部连接看不到任何一行。"""
    connection = _shared(tmp_path, "atomicity")
    witness = _witness(connection)
    first_write_done = threading.Event()
    release = threading.Event()
    seen_inside: list[int] = []

    def operation() -> None:
        with connection:
            _insert_task(connection, "a1")
            first_write_done.set()
            assert release.wait(10)
            _insert_task(connection, "a2")

    worker = threading.Thread(target=operation)
    worker.start()
    try:
        assert first_write_done.wait(10)
        seen_inside.append(_count(witness))  # 外部连接在块中途看
        release.set()
        worker.join(timeout=10)
        after = _count(witness)
    finally:
        release.set()
        worker.join(timeout=10)
        witness.close()
        connection.close()
    assert seen_inside == [0], "块未退出时外部连接不该看到半个操作"
    assert after == 2, "块退出后该操作的两行应同时可见"


def test_a_failing_block_no_longer_rolls_back_another_operations_write(tmp_path: Path) -> None:
    """AC-03（回归，探针 3 原样重放）：A 的块无异常、B 的块抛错 ⇒ A 的写仍在。

    收口前：外部连接看到 **两行全无**（A 已完成的操作被 B 的失败回滚掉）。
    """
    connection = _shared(tmp_path, "rollback_radius")
    witness = _witness(connection)
    a_finished = threading.Event()
    b_running = threading.Event()

    def operation_a() -> None:
        with connection:
            _insert_task(connection, "a1")
            a_finished.set()
            b_running.wait(10)

    def operation_b() -> None:
        with pytest.raises(RuntimeError):
            with connection:
                b_running.set()
                _insert_task(connection, "b1")
                raise RuntimeError("operation B failed after its first write")

    a = threading.Thread(target=operation_a)
    b = threading.Thread(target=operation_b)
    a.start()
    b.start()
    a.join(timeout=15)
    b.join(timeout=15)
    rows = [row[0] for row in witness.execute("SELECT task_id FROM tasks").fetchall()]
    witness.close()
    connection.close()
    assert rows == ["a1"], "B 的失败只能回滚 B 自己；A 已完成的操作必须留下"


def test_another_thread_cannot_commit_a_block_that_is_in_flight(tmp_path: Path) -> None:
    """AC-04（回归，探针 2 原样重放）：A 在块内时，B 的块必须等它退出。"""
    connection = _shared(tmp_path, "no_midway_commit")
    witness = _witness(connection)
    a_in_block = threading.Event()
    a_may_exit = threading.Event()
    b_done = threading.Event()
    seen_by_b: list[int] = []

    def operation_a() -> None:
        with connection:
            _insert_task(connection, "a1")
            a_in_block.set()
            a_may_exit.wait(10)

    def operation_b() -> None:
        with connection:
            # 只记"进块时共享连接自己看得见几行"——witness 是本线程创建的连接，
            # 不能跨线程用（sqlite3 的线程检查），外部视角统一由主线程看。
            seen_by_b.append(int(connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]))
        b_done.set()

    a = threading.Thread(target=operation_a)
    b = threading.Thread(target=operation_b)
    a.start()
    assert a_in_block.wait(10)
    b.start()
    try:
        assert not b_done.wait(BLOCK_WAIT_SECONDS), "A 的块还开着 ⇒ B 的块进不来"
        assert _count(witness) == 0, "块未退出 ⇒ 外部连接看不到 A 的行"
    finally:
        a_may_exit.set()
        a.join(timeout=10)
        b.join(timeout=10)
    assert b_done.is_set()
    assert seen_by_b == [1], "A 退出后 B 才进块，此时应看到 A 那行已提交"
    assert _count(witness) == 1
    witness.close()
    connection.close()


def test_the_block_lock_is_released_even_when_the_exit_commit_fails(tmp_path: Path) -> None:
    """AC-05（确定性）：提交抛错也必须把锁还回去，否则整条连接永久卡死。"""
    connection = _shared_that_fails_to_commit(tmp_path)
    try:
        with pytest.raises(RuntimeError):
            with connection:
                _insert_task(connection, "a1")
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(lambda: connection.execute("SELECT 1").fetchone())
            assert pending.result(timeout=BLOCK_WAIT_SECONDS) is not None
    finally:
        connection.close()


def test_nested_blocks_in_one_thread_do_not_deadlock(tmp_path: Path) -> None:
    """AC-07（回归）：同线程嵌套块是可重入的；外层退出后锁是空的。"""
    connection = _shared(tmp_path, "nested")
    witness = _witness(connection)
    try:
        with connection:
            _insert_task(connection, "a1")
            with connection:
                _insert_task(connection, "a2")
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(
                lambda: connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
            )
            assert pending.result(timeout=BLOCK_WAIT_SECONDS) == 2
        assert _count(witness) == 2
    finally:
        witness.close()
        connection.close()


def test_a_failing_block_still_swallows_nothing(tmp_path: Path) -> None:
    """AC-07（回归）：块内异常向外抛（与真连接一致），且该块的写被回滚。"""
    connection = _shared(tmp_path, "propagate")
    witness = _witness(connection)
    try:
        with pytest.raises(RuntimeError):
            with connection:
                _insert_task(connection, "a1")
                raise RuntimeError("boom")
        assert _count(witness) == 0
    finally:
        witness.close()
        connection.close()


# 白名单＝构造期的 schema bootstrap（本连接的初始化，不是并发写路径）
# ＋ 事务边界本身的实现（它就在块内提交，但没有可供 AST 识别的 `with` 语句）。
_BOOTSTRAP_COMMIT = {
    ("catalog_override_store.py", "__init__"),
    ("eval_report_store.py", "_ensure_compatible_schema"),
    ("evidence_ledger.py", "__init__"),
    ("experiment_store.py", "__init__"),
    ("library_store.py", "__init__"),
    ("memory_store.py", "__init__"),
    ("project_store.py", "__init__"),
    ("worker_registry.py", "__init__"),
    ("db.py", "_exit_context"),
}


def _inside_with(function: ast.FunctionDef, target: ast.AST) -> bool:
    """target 是否落在该函数内某个 `with` 块的语句体里。"""
    for node in ast.walk(function):
        if isinstance(node, ast.With) and any(target is inner for inner in ast.walk(node)):
            return True
    return False


def _bare_commits(path: Path) -> set[tuple[str, str]]:
    """`adapters/sqlite/*.py` 里**不在 `with` 块内**的 `.commit()` 调用（按函数名）。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[tuple[str, str]] = set()
    for function in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        for node in ast.walk(function):
            if not isinstance(node, ast.Call):
                continue
            if not (isinstance(node.func, ast.Attribute) and node.func.attr == "commit"):
                continue
            if not _inside_with(function, node):
                found.add((path.name, function.name))
    return found


def test_write_paths_commit_only_inside_a_transaction_block() -> None:
    """AC-06（结构门禁）：除构造期 bootstrap 外，写路径不得裸 `commit()`。

    裸 `commit()` 提交的是**整条连接**上待提交的一切，而不是调用方自己的那几条语句；
    在共享连接上它等于"替别人的半个操作签字"。白名单只有构造期的 schema bootstrap
    （本连接的初始化，不是并发写路径），出现新的一处就会红。
    """
    root = Path(__file__).resolve().parents[3] / "adapters" / "sqlite"
    offenders: set[tuple[str, str]] = set()
    for path in sorted(root.glob("*.py")):
        offenders |= _bare_commits(path)
    assert offenders == _BOOTSTRAP_COMMIT, (
        "写路径出现裸 commit（或在 with 块外提交）："
        f"{sorted(offenders - _BOOTSTRAP_COMMIT)}；白名单里已消失的："
        f"{sorted(_BOOTSTRAP_COMMIT - offenders)}"
    )


class _SharedThatFailsToCommit(SerializedConnection):
    """共享连接 + 故障注入：`commit()` 必抛（用来验"提交失败也要把锁还回去"）。

    覆盖的是 `commit` 本身，不是 `_commit_txn`：父类的 `commit = _commit_txn` 是
    **类创建时**绑定的函数对象，子类改 `_commit_txn` 不会改到 `commit`。
    """

    def commit(self) -> None:
        raise RuntimeError("injected commit failure")


def _shared_that_fails_to_commit(tmp_path: Path) -> SerializedConnection:
    """建好 schema 的"提交必失败"连接（`connect()` 固定用 SerializedConnection 工厂）。"""
    connection = _SharedThatFailsToCommit(
        str(tmp_path / "commit_fails.db"), check_same_thread=False
    )
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA_SQL)
    return connection
