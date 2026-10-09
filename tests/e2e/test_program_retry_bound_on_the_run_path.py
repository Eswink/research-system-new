"""GOAL-20261009-041 EC-04 判据：**重试的上界在崩溃窗口下也成立**（实跑 + 反证）。

靶子（EC-04 (a)(b)(c)）：程序声明 `max_attempts_per_index=N`，第 1 轮以 `FAILED` 收敛，
而在**认领了同序号却未落库**（崩溃窗口）之后继续推进 ——

- (a) 判定**必须收敛**：序列以 `STOP_RUN_FAILED` 收口（点名「重试已用尽」与上界）；
- (b) **反证臂**：任何形态下**不得**出现无界的 `RETRY_FAILED_RUN` 序列
  （收口所需的推进次数 **≤** 声明上界，且**始终不产生**第二个同序号 run）；
- (c) 中间形态**可区分**：崩溃窗口落 `DEDUP_FAILED_RUN`（与结论面的 `DEDUP` **不同面**），
  且它**计入**已用尝试数；
- (d) 缺省（不声明重试）行为**逐字不变** ⇒ `STOP_RUN_FAILED`（不隐式重跑）。

**崩溃窗口怎么造**（承 GOAL-20261008-037 EC-04 的既有手法）：经**产品路径**起 run 之后，
直接向 store 落一条 `RETRY_FAILED_RUN` 决策、其 `cited_run_id` 是一个**不存在**的 id ——
这**就是**「启动面返回了 id 而该 run 没有落库」的等价形态（`_start_run_for_program` 先落 run
行再执行 ⇒ 真实崩溃窗口正是「决策已落、行未落」）。**判据读的是既有读面**
（`GET /programs/{id}`），不经内部对象推断。
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from packages.domain.core import Timestamp
from packages.domain.program import ProgramDecision, ProgramDecisionKind
from services.api.app import create_app
from tests.e2e.cross_run_support import PROTOCOL, cross_run_deps
from tests.e2e.program_advance_support import advance, create_program, read_program

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

_STOP_RUN_FAILED = "STOP_RUN_FAILED"
_RETRY_FAILED_RUN = "RETRY_FAILED_RUN"
_DEDUP_FAILED_RUN = "DEDUP_FAILED_RUN"


def _failing_program(client: TestClient, *, max_attempts_per_index: int) -> tuple[str, str]:
    """建程序（声明重试）+ 起第 1 轮（受控执行体不给交付物 ⇒ 必然 `FAILED`）。

    返回 `(程序 id, 第 1 轮 run id)`。
    """
    program = create_program(
        client,
        max_runs=3,
        protocol=PROTOCOL,
        max_attempts_per_index=max_attempts_per_index,
    )
    program_id = str(program["id"])
    first = advance(client, program_id)
    run_id = str(first["started_run_id"])
    detail = read_program(client, program_id)
    assert [row["state"] for row in detail["runs"]] == ["FAILED"], detail["runs"]
    return program_id, run_id


def _seed_claimed_but_missing(deps: Any, program_id: str, index: int, claim: str) -> None:
    """预置「认领了该序号而 run 未落库」的决策（真实崩溃窗口的等价形态）。"""
    store = deps.program_store
    assert store is not None
    store.record_decision(
        ProgramDecision(
            program_id=program_id,
            after_index=index,
            kind=ProgramDecisionKind.RETRY_FAILED_RUN,
            reason="（测试预置）上一条沿用了真实形态的重试认领",
            cited_run_id=claim,
            cited_facts=("state=FAILED", "attempts=1/3"),
            decided_at=Timestamp.now(),
        )
    )


def _failing_deps() -> Any:
    """第 1 轮**必然失败**的装配（受控执行体不给任何交付物 ⇒ 门判拒）。"""
    from dataclasses import replace

    from packages.application.run_orchestration.service import RunOrchestrationService
    from tests.e2e.scenario import StructuredOutputAgentRuntime

    deps = cross_run_deps()
    inner = deps.runs._deps
    deps.runs = RunOrchestrationService(
        replace(inner, runtime=StructuredOutputAgentRuntime(outputs_by_contract={}))
    )
    return deps


def test_the_retry_bound_holds_across_repeated_crash_windows() -> None:
    """(a)(b) 实跑：一次「认领即崩」之后反复推进 ⇒ 判定在 ≤ 声明上界内收口到
    `STOP_RUN_FAILED`（上界在崩溃模式下也成立）。"""
    allowed = 3
    deps = _failing_deps()
    with TestClient(create_app(deps)) as client:
        program_id, run_id = _failing_program(client, max_attempts_per_index=allowed)
        # 一次崩溃窗口：认领了序号 1 而那条 run 没有落库。
        _seed_claimed_but_missing(deps, program_id, 1, "ghost-0001")
        kinds: list[str] = []
        for _round_no in range(allowed + 2):
            result = advance(client, program_id)
            kinds.append(str(result["decision"]["kind"]))
            if kinds[-1] == _STOP_RUN_FAILED:
                break
        # (a) 必须收口，且**不超**声明上界（上界在任意崩溃模式下都成立）。
        assert kinds[-1] == _STOP_RUN_FAILED, ("判定必须收敛到失败停", kinds)
        assert len(kinds) <= allowed, ("收口步数不得超过声明上界", allowed, kinds)
        # (b) 反证臂：中间形态是**去重**（不是继续重试）——否则就是无界重跑。
        assert kinds[0] == _DEDUP_FAILED_RUN, ("崩溃窗口必须先落去重事实", kinds)
        detail = read_program(client, program_id)
        # 去重：**始终不产生**第二个同序号 run。
        assert [row["program_index"] for row in detail["runs"]] == [1], detail["runs"]
        assert [row["run_id"] for row in detail["runs"]] == [run_id]
        assert detail["run_count"] == 1
        stop = detail["decisions"][-1]
        assert stop["kind"] == _STOP_RUN_FAILED
        assert any(f"attempts={allowed}/{allowed}" in item for item in stop["cited_facts"]), stop
        assert "重试已用尽" in stop["reason"], stop
        assert "未获结论" in stop["reason"], stop


def test_the_crash_window_dedup_is_distinguishable_and_counted() -> None:
    """(c) 中间形态可区分：崩溃窗口落 `DEDUP_FAILED_RUN`（**不是**结论面的 `DEDUP`），
    且它把**已用尝试数**推高一格（否则上界可被反复绕过）。"""
    deps = _failing_deps()
    with TestClient(create_app(deps)) as client:
        program_id, _run_id = _failing_program(client, max_attempts_per_index=3)
        _seed_claimed_but_missing(deps, program_id, 1, "ghost-single")
        result = advance(client, program_id)
        decision = result["decision"]
        assert decision["kind"] == _DEDUP_FAILED_RUN, decision
        assert decision["kind"] != "DEDUP", ("两面不得混用（结论面认领的是下一序号）", decision)
        assert decision["cited_run_id"] == "ghost-single", decision
        assert result["started_run_id"] is None, "未落库的认领不得被重复起"
        facts = decision["cited_facts"]
        assert any("attempts=2/3" in item for item in facts), (
            "被阻塞的推进必须计入已用尝试数（否则上界可被无限绕过）",
            facts,
        )
        assert any("claimed run ghost-single" in item for item in facts), facts
        assert read_program(client, program_id)["run_count"] == 1


def test_the_default_declaration_is_unchanged_by_this_goal() -> None:
    """(d) 缺省（`max_attempts_per_index` 未声明 ⇒ 1）⇒ 行为**逐字不变**：失败停、不重跑。"""
    deps = _failing_deps()
    with TestClient(create_app(deps)) as client:
        program = create_program(client, max_runs=3, protocol=PROTOCOL)
        program_id = str(program["id"])
        assert program["max_attempts_per_index"] == 1, program
        advance(client, program_id)
        second = advance(client, program_id)
        assert second["decision"]["kind"] == _STOP_RUN_FAILED, second["decision"]
        assert second["started_run_id"] is None
        assert "未声明重试" in second["decision"]["reason"], second["decision"]["reason"]
        detail = read_program(client, program_id)
        assert [row["program_index"] for row in detail["runs"]] == [1]


def test_a_landed_retry_still_uses_the_retry_face() -> None:
    """**反证臂（不该红时不红）**：正常落库的重试仍走 `RETRY_FAILED_RUN` + 同序号新 run
    —— 本轮不得把「落库的重试」误判成崩溃窗口。"""
    deps = _failing_deps()
    with TestClient(create_app(deps)) as client:
        program_id, first_run_id = _failing_program(client, max_attempts_per_index=2)
        result = advance(client, program_id)
        assert result["decision"]["kind"] == _RETRY_FAILED_RUN, result
        assert result["started_run_id"], result
        detail = read_program(client, program_id)
        indices = sorted(row["program_index"] for row in detail["runs"])
        assert indices == [1, 1], ("重试是**同序号**（不推进轮次）", indices)
        assert len({row["run_id"] for row in detail["runs"]}) == 2, detail["runs"]
        assert first_run_id in {row["run_id"] for row in detail["runs"]}


def test_the_program_read_face_keeps_every_advance_as_a_decision() -> None:
    """**存储面的静默丢弃**（本轮实测的第二个缺陷）：一次推进 = 一条决策，
    即使多次推进落在**同一时钟刻度**（微秒相同）也**不得**互相顶掉。"""
    deps = _failing_deps()
    with TestClient(create_app(deps)) as client:
        program_id, _run_id = _failing_program(client, max_attempts_per_index=4)
        kinds: list[str] = []
        for round_no in range(6):
            kinds.append(str(advance(client, program_id)["decision"]["kind"]))
            if kinds[-1] == _STOP_RUN_FAILED:
                break
        detail = read_program(client, program_id)
        decisions = detail["decisions"]
        # 推进次数 = 起的 run（1 START）+ 之后每次推进一条 ⇒ 决策数必须与推进次数一致。
        assert len(decisions) == len(kinds) + 1, (
            "每次推进都必须留下一条可读决策（紧循环里不得静默丢弃）",
            len(kinds),
            len(decisions),
        )
        stamps = [row["decided_at"] for row in decisions]
        assert stamps == sorted(stamps), ("决策时点必须单调（读面顺序事实）", stamps)
        assert len(set(stamps)) == len(stamps), ("自然键不得碰撞", stamps)


def test_every_advance_is_readable_under_a_tight_loop() -> None:
    """读面自洽：一次崩溃窗口之后紧循环推进，决策序列里 `DEDUP_FAILED_RUN` /
    `RETRY_FAILED_RUN` / `STOP_RUN_FAILED` **各自留痕**（不是只剩最后一条）。"""
    deps = _failing_deps()
    with TestClient(create_app(deps)) as client:
        program_id, _run_id = _failing_program(client, max_attempts_per_index=3)
        _seed_claimed_but_missing(deps, program_id, 1, "ghost-loop")
        for _round_no in range(3):
            advance(client, program_id)
        kinds = [row["kind"] for row in read_program(client, program_id)["decisions"]]
        assert _RETRY_FAILED_RUN in kinds, kinds
        assert _DEDUP_FAILED_RUN in kinds, kinds
        assert _STOP_RUN_FAILED in kinds, kinds
        assert kinds[-1] == _STOP_RUN_FAILED, ("失败停必须是收口形态", kinds)
