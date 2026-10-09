"""GOAL-20261008-040 EC-04 判据：**停止理由在实跑路径上可区分**（失败面 / 取消面 / 重试）。

靶子（EC-04 (a)(b)(c)(d)）：程序推进按上一轮**终态**分派 ——

- 第 1 轮**执行失败**（受控执行体不给必需交付物）⇒ 推进落 `STOP_RUN_FAILED`，
  **点名**「未获结论」与 `state=FAILED`（**不是** `STOP_RULE` + 空 `cited_facts`）；
- 声明重试（`max_attempts_per_index=2`）⇒ 落 `RETRY_FAILED_RUN`、**同序号**重起、计数可见；
  再用尽 ⇒ `STOP_RUN_FAILED` + 点名上界；
- **反证臂**：任何形态下**不得**出现「`STOP_RULE` + `cited_facts == []`」；
- 缺省（`max_attempts_per_index` 未声明）⇒ 行为 = 失败停（**不**隐式重跑）。

**为什么这属于深度轴**：「轮数由**结论**驱动」—— 而失败轮**没有结论**；
把「没有结论」读成「结论说停」会让读面无法分辨「研究完成、结论说不必再轮」与「这轮没跑成」。
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from services.api.app import create_app
from tests.e2e.cross_run_support import PROTOCOL, cross_run_deps
from tests.e2e.program_advance_support import advance, create_program, read_program

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

_STOP_RUN_FAILED = "STOP_RUN_FAILED"
_RETRY_FAILED_RUN = "RETRY_FAILED_RUN"
_STOP_RULE = "STOP_RULE"


def _failing_deps() -> Any:
    """装配一个**必然失败**的第 1 轮：受控执行体不给任何交付物 ⇒ 门判拒 / 执行失败。"""
    from dataclasses import replace

    from packages.application.run_orchestration.service import RunOrchestrationService
    from tests.e2e.scenario import StructuredOutputAgentRuntime

    deps = cross_run_deps()
    inner = deps.runs._deps
    deps.runs = RunOrchestrationService(
        replace(inner, runtime=StructuredOutputAgentRuntime(outputs_by_contract={}))
    )
    return deps


def _advance_twice(
    deps: Any, *, retry: int | None = None
) -> tuple[TestClient, dict[str, Any], dict[str, Any]]:
    """建程序（可选声明重试）+ 推进一次（起失败轮）+ 再推进一次（观测失败面判定）。"""
    client = TestClient(create_app(deps)).__enter__()
    # 声明走**产品路径**（建程序时给）—— 不绕过写面去改 canonical 行。
    program = create_program(
        client,
        max_runs=3,
        protocol=PROTOCOL,
        max_attempts_per_index=retry if retry is not None else 1,
    )
    assert program["max_attempts_per_index"] == (retry if retry is not None else 1), program
    first = advance(client, str(program["id"]))
    second = advance(client, str(program["id"]))
    return client, first, second


def test_a_failed_round_is_stopped_by_failure_with_the_reason_named() -> None:
    """(a) 实跑：失败轮 ⇒ `STOP_RUN_FAILED`，判词点名「未获结论」与 `state=FAILED`。"""
    client, first, second = _advance_twice(_failing_deps())
    try:
        assert first["decision"]["kind"] == "START"
        detail = read_program(client, str(first["program_id"]))
        assert detail["runs"][0]["state"] == "FAILED", detail["runs"]
        assert second["decision"]["kind"] == _STOP_RUN_FAILED, second["decision"]
        assert second["decision"]["cited_facts"], "失败停必须点名（空数组是旧形态）"
        assert "state=FAILED" in second["decision"]["cited_facts"]
        assert "未获结论" in second["decision"]["reason"]
        assert second["started_run_id"] is None, "缺省不重试"
    finally:
        client.__exit__(None, None, None)


def test_the_old_conclusion_stop_shape_never_appears_for_a_failed_round() -> None:
    """(c) **反证臂**：失败轮**不得**再落「`STOP_RULE` + 空 `cited_facts`」（本轮要消灭的形态）。"""
    client, _first, second = _advance_twice(_failing_deps())
    try:
        decision = second["decision"]
        assert not (decision["kind"] == _STOP_RULE and not decision["cited_facts"]), (
            "「没有结论」不得被读成「结论说停」",
            decision,
        )
    finally:
        client.__exit__(None, None, None)


def test_a_declared_retry_restarts_the_same_index_then_stops_when_exhausted() -> None:
    """(b) 声明重试：失败后落 `RETRY_FAILED_RUN` 且**同序号**重起；用尽 ⇒ `STOP_RUN_FAILED`。"""
    client, first, second = _advance_twice(_failing_deps(), retry=2)
    try:
        assert second["decision"]["kind"] == _RETRY_FAILED_RUN, second["decision"]
        assert second["started_run_id"], second
        detail = read_program(client, str(first["program_id"]))
        indices = [row["program_index"] for row in detail["runs"]]
        assert indices == [1, 1], ("重试是**同序号**（不推进轮次）", indices)
        assert any("attempts=1/2" in item for item in second["decision"]["cited_facts"])
        third = advance(client, str(first["program_id"]))
        assert third["decision"]["kind"] == _STOP_RUN_FAILED, third["decision"]
        assert any("attempts=2/2" in item for item in third["decision"]["cited_facts"])
        assert "重试已用尽" in third["decision"]["reason"]
        assert third["started_run_id"] is None
    finally:
        client.__exit__(None, None, None)


def test_the_default_declaration_stops_without_retrying() -> None:
    """(d) 缺省：不声明重试 ⇒ 失败停（**不**隐式重跑），且理由点名「未声明重试」。"""
    client, _first, second = _advance_twice(_failing_deps())
    try:
        assert second["decision"]["kind"] == _STOP_RUN_FAILED
        assert "未声明重试" in second["decision"]["reason"], second["decision"]["reason"]
        assert second["started_run_id"] is None
        detail = read_program(client, str(second["program_id"]))
        assert [row["program_index"] for row in detail["runs"]] == [1], detail["runs"]
    finally:
        client.__exit__(None, None, None)
