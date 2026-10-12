"""GOAL-20261012-060（序 28）：**混合式闸门经产品路径真的停得住** —— EC-03 的产品面判据。

**为什么单列**：`tests/application/run_orchestration/test_program_hybrid_gate_on_the_run_path.py`
判**判定值**（两维各自点名）；本文件判**产品路径真的接上了** —— 经既有 HTTP 面建程序时
声明混合式，第 1 轮跑完（本可续跑）后的推进必须**停下等人**且读面把声明回显。

**四态逐条**（与 HTTP 面判据同族）：

1. **序号维命中**（`at_indexes=[1]`，判词不命中）⇒ 停 + 读面回显两维；
2. **条件维命中**（`on_verdicts=["PASS"]`，第 1 轮不是点）⇒ 停 + 读面回显；
3. **反证臂①**：未声明 ⇒ 同一实跑逐字走结论面（`CONTINUE`）—— 既有行为不变；
4. **反证臂②**：声明了但两维都不命中 ⇒ 照常 `CONTINUE`（不是「声明了就停」）。

**如实边界**：本文件不判裁决 / 恢复面（那是序 15/16/23 的既有判据）。
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from services.api.app import create_app
from tests.e2e.program_advance_support import advance, create_program, program_deps, read_program

_START = "START"
_CONTINUE = "CONTINUE"
_WAIT_FOR_APPROVAL = "WAIT_FOR_APPROVAL"


def _program_id(recent: dict[str, Any]) -> str:
    return str(recent["id"])


def test_a_declared_hybrid_gate_stops_the_http_advance_on_the_index_dimension() -> None:
    """EC-03 ①：**序号维**命中 ⇒ 停在闸门等人（判词点名该维 + 读面回显两维）。"""
    with TestClient(create_app(program_deps())) as client:
        program = create_program(
            client,
            max_runs=3,
            human_gate_hybrid={"at_indexes": [1], "on_verdicts": ["REJECT"]},
        )
        assert program["human_gate_hybrid"] == {
            "at_indexes": [1],
            "on_verdicts": ["REJECT"],
        }, ("建程序回执必须回显声明", program)
        assert advance(client, _program_id(program))["decision"]["kind"] == _START
        second = advance(client, _program_id(program))
        assert second["decision"]["kind"] == _WAIT_FOR_APPROVAL, second
        assert "at_indexes=[1]" in second["decision"]["reason"], second["decision"]
        assert second["started_run_id"] is None, "等人拍板时不得起新轮"
        detail = read_program(client, _program_id(program))
        assert detail["human_gate_hybrid"] == {"at_indexes": [1], "on_verdicts": ["REJECT"]}
        assert detail["run_count"] == 1, "第 2 轮不得被起（闸门拦住）"


def test_a_declared_hybrid_gate_stops_the_http_advance_on_the_condition_dimension() -> None:
    """EC-03 ②：**条件维**命中 ⇒ 同样停下等人（第 1 轮不是声明的点 ⇒ 只有条件维）。"""
    with TestClient(create_app(program_deps())) as client:
        program = create_program(
            client,
            max_runs=3,
            human_gate_hybrid={"at_indexes": [3], "on_verdicts": ["PASS"]},
        )
        assert advance(client, _program_id(program))["decision"]["kind"] == _START
        second = advance(client, _program_id(program))
        assert second["decision"]["kind"] == _WAIT_FOR_APPROVAL, second
        assert "on_verdicts=['PASS']" in second["decision"]["reason"], second["decision"]
        assert second["started_run_id"] is None


def test_an_undeclared_hybrid_leaves_the_http_advance_verbatim() -> None:
    """EC-03 反证臂①：**未声明** ⇒ 同一实跑逐字走结论面（`CONTINUE`，既有行为不变）。"""
    with TestClient(create_app(program_deps())) as client:
        program = create_program(client, max_runs=3)
        assert program["human_gate_hybrid"] is None, program
        assert advance(client, _program_id(program))["decision"]["kind"] == _START
        second = advance(client, _program_id(program))
        assert second["decision"]["kind"] == _CONTINUE, second
        assert "混合式" not in second["decision"]["reason"], second["decision"]
        assert read_program(client, _program_id(program))["run_count"] == 2, "缺省路径照常续跑"


def test_a_declared_hybrid_that_misses_both_dimensions_continues() -> None:
    """EC-03 反证臂②：声明了但**两维都不命中** ⇒ 照常续跑（不是「声明了就停」）。"""
    with TestClient(create_app(program_deps())) as client:
        program = create_program(
            client,
            max_runs=3,
            human_gate_hybrid={"at_indexes": [3], "on_verdicts": ["REJECT"]},
        )
        assert advance(client, _program_id(program))["decision"]["kind"] == _START
        second = advance(client, _program_id(program))
        assert second["decision"]["kind"] == _CONTINUE, second
        assert "混合式" not in second["decision"]["reason"], second["decision"]
        assert read_program(client, _program_id(program))["run_count"] == 2
