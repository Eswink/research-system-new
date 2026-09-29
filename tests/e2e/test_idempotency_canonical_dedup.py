"""GOAL-026 EC-01（AC-2）：域级去重按 **canonical 行计数**取证（含两向控制）。

既有判据（`tests/e2e/test_idempotency.py`）断言「重复 submit **不新增**行」。
本判据补上它没有的两点（承 MEM-156 / MEM-159）：

1. **恰为一行** —— 同键重放前后 `tasks` 与 `idempotency_records` 的行数不变且 **== 1**；
2. **异键 ⇒ 第二行应当出现**（行数 **== 2**）—— 证明上面的计数判据**不是空转**：
   如果去重把**所有**提交都吞掉，第二条断言会红。

SQL 一律是**字面量直送** `execute`（不经过任何变量或拼接）。
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import replace

from adapters.sqlite.db import connect
from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.domain.core import ID
from tests.contracts.fixtures import research_task, task_contract


def _count_tasks(connection: sqlite3.Connection) -> int:
    row = connection.execute("SELECT COUNT(*) FROM tasks").fetchone()
    return int(row[0])


def _count_idempotency_records(connection: sqlite3.Connection) -> int:
    row = connection.execute("SELECT COUNT(*) FROM idempotency_records").fetchone()
    return int(row[0])


def _submit_with_key(engine: SqliteWorkflowEngine, key: str | None) -> None:
    """同 run、**新 task id**、给定去重键的一次提交。"""
    first = research_task()
    engine.submit(replace(first, id=ID(str(uuid.uuid4())), idempotency_key=key), task_contract())


def test_same_idempotency_key_leaves_exactly_one_business_fact() -> None:
    """同键重放 ⇒ canonical 层**恰为一条**业务事实（两张表都数）。"""
    connection = connect(":memory:")
    engine = SqliteWorkflowEngine(connection=connection)
    try:
        task = research_task()
        engine.submit(task, task_contract())
        assert task.idempotency_key is not None
        _submit_with_key(engine, task.idempotency_key)
        assert _count_tasks(connection) == 1
        assert _count_idempotency_records(connection) == 1
    finally:
        engine.close()


def test_a_different_idempotency_key_produces_a_second_business_fact() -> None:
    """**两向控制**：换一个键 ⇒ 第二条业务事实**应当**出现（否则计数判据是空真）。"""
    connection = connect(":memory:")
    engine = SqliteWorkflowEngine(connection=connection)
    try:
        engine.submit(research_task(), task_contract())
        _submit_with_key(engine, "idem-second-key")
        assert _count_tasks(connection) == 2
        assert _count_idempotency_records(connection) == 2
    finally:
        engine.close()
