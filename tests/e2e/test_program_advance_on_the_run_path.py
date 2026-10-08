"""GOAL-20261008-037 EC-02 判据：**程序跨两次 run 推进，且由上一轮落库结论驱动**。

靶子（EC-02 (a)(b)(c)(d)）：经**既有 HTTP 面**建程序并推进两次 ——

- 第 1 轮：程序内还没有 run ⇒ 决策 `START`，起第 1 轮（经既有 start-run 链：
  preflight → freeze → execute），跑完落库逐条判词；
- 第 2 轮：**由第 1 轮落库判词**（`REVIEW_SCORE: review score 0.95 GTE 0.8` ⇒ 验收门
  `PASS`）命中声明式规则 ⇒ 决策 `CONTINUE`，起第 2 轮；
- 关联**落 canonical**：两轮 run 的 `program_id` / `program_index` 从 run 读面取到
  （不是日志/侧表/推断）。

四态逐条（每态独立用例，全部读**既有读面**）：

1. **继续**：`CONTINUE` + `started_run_id` 在场 + 程序内 run 数 = 2 + 两轮序号 1/2。
2. **结论停**：执行体给 `REJECT`（分数 0.5 < 0.8）⇒ 第 1 轮落库判词不含规则值 ⇒
   决策 `STOP_RULE` + **不**起第 2 轮（run 数仍 1）+ 判词**逐字**进 `cited_facts`。
3. **护栏停（与结论停可区分）**：`max_runs=1` + 结论面判「续」⇒ 决策 `STOP_GUARDRAIL`
   （种类与 `STOP_RULE` 不同）+ 理由点名上界 + **不**起第 2 轮。
4. **反证：缺启动面 ⇒ 点名**：把编排服务撤掉（`deps.runs=None`）⇒ 需要起 run 时决策
   落 `WAIT` 且理由**点名**「未提供启动面」（不静默 200 冒充已启动）。

**如实边界**（本文件不声称已解决）：第 2 轮**读到**第 1 轮的结论（跨 run 知识的**读入**）
是 EC-03 的事 —— 本文件只证「续跑由落库结论驱动」；程序级人工介入不在范围。
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from services.api.app import create_app
from tests.e2e.program_advance_support import (
    REJECT_OUTPUT,
    advance,
    create_program,
    program_deps,
    read_program,
)

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

_START = "START"
_CONTINUE = "CONTINUE"
_STOP_RULE = "STOP_RULE"
_STOP_GUARDRAIL = "STOP_GUARDRAIL"
_WAIT = "WAIT"


def _program_id(recent: dict[str, Any]) -> str:
    return str(recent["id"])


def test_first_advance_starts_round_one_and_binds_it_to_the_program() -> None:
    """`START`：程序内没有 run ⇒ 起第 1 轮，且关联落 canonical（run 读面可复核）。"""
    with TestClient(create_app(program_deps())) as client:
        program = create_program(client, max_runs=3)
        first = advance(client, _program_id(program))
        assert first["decision"]["kind"] == _START
        assert first["started_run_id"], first
        detail = read_program(client, _program_id(program))
        assert detail["run_count"] == 1
        assert detail["runs"][0]["state"] == "SUCCEEDED"
        assert detail["runs"][0]["manifest_digest"], "冻结必须真的发生"
        run = client.get(f"/runs/{first['started_run_id']}").json()
        assert run["program_id"] == _program_id(program)
        assert run["program_index"] == 1


def test_second_advance_is_driven_by_the_recorded_verdict() -> None:
    """`CONTINUE`：上一轮落库判词命中规则 ⇒ 起第 2 轮；决策带**逐字**判词。"""
    with TestClient(create_app(program_deps())) as client:
        program = create_program(client, max_runs=3)
        advance(client, _program_id(program))
        second = advance(client, _program_id(program))
        assert second["decision"]["kind"] == _CONTINUE, second
        assert second["decision"]["cited_facts"], "被引事实必须是判词原文"
        assert second["decision"]["cited_facts"] == ["verdict PASS"], second
        assert second["started_run_id"]
        detail = read_program(client, _program_id(program))
        assert detail["run_count"] == 2
        assert [row["program_index"] for row in detail["runs"]] == [1, 2]
        assert all(row["state"] == "SUCCEEDED" for row in detail["runs"])


def test_a_rejected_verdict_stops_the_program_by_conclusion() -> None:
    """`STOP_RULE`：落库判词**不**命中规则 ⇒ 按结论停（不起第 2 轮）。"""
    with TestClient(create_app(program_deps(output=REJECT_OUTPUT))) as client:
        program = create_program(client, max_runs=3)
        advance(client, _program_id(program))
        second = advance(client, _program_id(program))
        assert second["decision"]["kind"] == _STOP_RULE, second
        assert second["started_run_id"] is None
        assert "verdict REJECT" in second["decision"]["cited_facts"], (
            "落库判词必须**逐字**进决策（不笼统「评审不通过」）",
            second,
        )
        assert read_program(client, _program_id(program))["run_count"] == 1


def test_the_guardrail_stop_is_distinguishable_from_the_conclusion_stop() -> None:
    """`STOP_GUARDRAIL`：结论面判「续」但已到上界 ⇒ 种类与理由都与结论停**可区分**。"""
    with TestClient(create_app(program_deps())) as client:
        program = create_program(client, max_runs=1)
        advance(client, _program_id(program))
        second = advance(client, _program_id(program))
        assert second["decision"]["kind"] == _STOP_GUARDRAIL, second
        assert second["decision"]["kind"] != _STOP_RULE
        assert "max_runs=1" in second["decision"]["reason"]
        assert second["started_run_id"] is None
        assert read_program(client, _program_id(program))["run_count"] == 1


def test_missing_start_face_is_named_not_faked() -> None:
    """反证：撤掉编排服务（需要起 run 时无启动面）⇒ `WAIT` 且**点名**，不静默。"""
    deps = program_deps()
    with TestClient(create_app(deps)) as client:
        program = create_program(client, max_runs=3)
    deps.runs = None
    with TestClient(create_app(deps)) as client:
        result = advance(client, _program_id(program))
        assert result["decision"]["kind"] == _WAIT, result
        assert "未提供启动面" in result["decision"]["reason"], result
        assert result["started_run_id"] is None
        assert read_program(client, _program_id(program))["run_count"] == 0


def test_advance_on_a_missing_program_is_404() -> None:
    """边界：推进不存在的程序 ⇒ 404（不伪装成空程序）。"""
    with TestClient(create_app(program_deps())) as client:
        response = client.post(
            "/programs/00000000-0000-4000-8000-000000000000/advance",
            headers={"Idempotency-Key": "advance-missing"},
        )
        assert response.status_code == 404, response.text
