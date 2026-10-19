"""GOAL-20261019-089 EC-03：**迭代自动起来**（第 N 轮终态后无需人工进入第 N+1 轮）。

**判什么**（逐条可证伪）：

1. **同一个词表 + 同一个装配**：`ScheduleJob` 含 `program_advance`，且守护线程
   `_execute_pass` 调的是 `program_advance.advance_for` —— **同一个函数**就是
   `POST /programs/{id}/advance` 用的那个（结构判据：两条调用点在同一模块里）。
2. **无人工进入下一轮**：程序第 1 轮跑完并落库 `PASS` ⇒ **只跑一次作业 pass**（不点
   HTTP 推进）⇒ 新 run 落库且 `program_index == 2`、决策种类 `CONTINUE`。
3. **闸门仍然停得住、理由可读**：声明 `human_gate_at_index=1` 的程序 ⇒ pass 后
   **不**起第 2 轮，且决策种类是 `WAIT_FOR_APPROVAL` 并点名待审批（既有三种闸门语义不动）。
4. **没有推进面就不假装有执行体**：`program_store` 缺席 ⇒ 作业不注册
   （`executor_attached == False`）。

判据用**真实 HTTP 面**建程序、真实编排跑 run（受控执行体），只把「谁触发推进」从
HTTP 换成作业 pass —— 这正是 EC-03 要证明的那一格。
"""

from __future__ import annotations

import inspect
from typing import Any

from fastapi.testclient import TestClient

from packages.domain.schedules import BUILTIN_NAMES, JOB_PURPOSE, ScheduleJob
from services.api.app import create_app
from services.api.program_advance import advance_for
from services.api.program_advance_scheduler import ProgramAdvanceScheduler
from tests.e2e.program_advance_support import (
    advance,
    create_program,
    program_deps,
    read_program,
)


def _client(deps: Any) -> TestClient:
    return TestClient(create_app(deps))


def test_the_job_is_in_the_vocabulary_with_its_own_purpose() -> None:
    assert ScheduleJob.PROGRAM_ADVANCE.value == "program_advance"
    assert "program_advance" in BUILTIN_NAMES
    assert JOB_PURPOSE[ScheduleJob.PROGRAM_ADVANCE]


def test_the_job_calls_the_same_assembly_as_the_manual_endpoint() -> None:
    """**结构判据**：作业的 pass 与 HTTP 端点是**同一个装配函数**（不建第二套）。

    两处源码都出现 `advance_for(`（作业里直接调用、端点里也直接调用），而
    `advance_for` 只在 `program_advance.py` 里定义一次 —— 「同一条链」因此可机械复核。
    """
    from services.api.routers import programs as programs_router

    assert advance_for.__module__ == "services.api.program_advance"
    worker_source = inspect.getsource(ProgramAdvanceScheduler)
    endpoint_source = inspect.getsource(programs_router)
    assert "advance_for(" in worker_source
    assert "advance_for(" in endpoint_source
    # 端点不再自己拼一份 advance_program 装配（第二套语义在结构上不存在）。
    assert "advance_program(" not in endpoint_source


def test_a_finished_round_advances_without_any_manual_call() -> None:
    """第 1 轮 `PASS` 落库 ⇒ 作业 pass 一次 ⇒ **第 2 轮自己起来**。"""
    deps = program_deps()
    with _client(deps) as client:
        program = create_program(client, max_runs=3, continue_on=["PASS"])
        # 第 1 轮：人工建程序后仍需**第一次**推进（程序里还没有 run）。
        advance(client, program["id"])
        first = read_program(client, program["id"])
        assert [item["program_index"] for item in first["runs"]] == [1], first["runs"]
        assert first["runs"][0]["state"] == "SUCCEEDED", first["runs"]

        # 从这里开始**不再**调用 HTTP 推进：只跑作业的一次 pass。
        scheduler = ProgramAdvanceScheduler(deps)
        report = scheduler._execute_pass()
        assert report["advanced"] == 1, report
        assert report["started"] == 1, report

        after = read_program(client, program["id"])
        assert [item["program_index"] for item in after["runs"]] == [1, 2], after["runs"]
        last = after["decisions"][-1]
        assert last["kind"] == "CONTINUE", last
        assert "verdict PASS" in " ".join(last["cited_facts"]), last


def test_a_declared_gate_still_stops_the_program_with_a_readable_reason() -> None:
    """声明了闸门 ⇒ 作业 pass **不**推进到下一轮，且理由点名（既有语义不动）。"""
    deps = program_deps()
    with _client(deps) as client:
        program = create_program(client, max_runs=3, continue_on=["PASS"], human_gate_at_index=1)
        advance(client, program["id"])
        first = read_program(client, program["id"])
        assert first["runs"][0]["state"] == "SUCCEEDED", first["runs"]

        scheduler = ProgramAdvanceScheduler(deps)
        report = scheduler._execute_pass()
        assert report["started"] == 0, report

        after = read_program(client, program["id"])
        assert [item["program_index"] for item in after["runs"]] == [1], after["runs"]
        last = after["decisions"][-1]
        assert last["kind"] == "WAIT_FOR_APPROVAL", last
        assert "approval" in last["reason"].lower() or "审批" in last["reason"], last


def test_without_a_program_store_no_executor_is_claimed() -> None:
    """没有程序存储 ⇒ 没有执行体（读面如实 `executor_attached=False`，不伪装）。"""
    deps = program_deps()
    deps.program_store = None
    with _client(deps) as client:
        payload = client.get("/ops/schedules").json()
        entry = {item["name"]: item for item in payload["schedules"]}["program_advance"]
        assert entry["executor_attached"] is False, entry
