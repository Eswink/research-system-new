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
2. **结论停**：那一轮**跑成**（`SUCCEEDED`）但落库判词不命中续跑规则 ⇒
   决策 `STOP_RULE` + **不**起第 2 轮（run 数仍 1）+ 判词**逐字**进 `cited_facts`。
   （形态：把 `continue_on` 声明成不命中上一轮判词的值。）
3. **失败停（与结论停可区分）**：执行体给 `REJECT`（分数 0.5 < 0.8）⇒ 那一轮以
   `FAILED` 收敛 ⇒ 决策 `STOP_RUN_FAILED`（**不是** `STOP_RULE`）+ 点名 `state=FAILED`
   + **不**起第 2 轮。
4. **护栏停（与结论停可区分）**：`max_runs=1` + 结论面判「续」⇒ 决策 `STOP_GUARDRAIL`
   （种类与 `STOP_RULE` 不同）+ 理由点名上界 + **不**起第 2 轮。
5. **反证：缺启动面 ⇒ 点名**：把编排服务撤掉（`deps.runs=None`）⇒ 需要起 run 时决策
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
_STOP_RUN_FAILED = "STOP_RUN_FAILED"
_STOP_GUARDRAIL = "STOP_GUARDRAIL"
_WAIT = "WAIT"
#: 声明的人工闸门拦下推进时的种类（GOAL-20261010-046 复用序 12 的同一类等待）。
_WAIT_FOR_APPROVAL = "WAIT_FOR_APPROVAL"


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


def test_a_rejected_verdict_stops_the_program_on_the_failure_face() -> None:
    """分数不达阈值 ⇒ 那一轮以 **FAILED** 收敛 ⇒ 走**失败面**（`STOP_RUN_FAILED`）。

    **GOAL-20261008-040 的行为修正（如实登记）**：本用例原先断言 `STOP_RULE` ——
    但实测那一轮的终态是 `FAILED`（验收门判拒 ⇒ 执行面失败）；旧代码把「这一轮跑失败了」
    读成「结论判续」正是本轮消灭的失真。现在它落 `STOP_RUN_FAILED` 并点名 `state=FAILED`。
    """
    with TestClient(create_app(program_deps(output=REJECT_OUTPUT))) as client:
        program = create_program(client, max_runs=3)
        advance(client, _program_id(program))
        second = advance(client, _program_id(program))
        assert second["decision"]["kind"] == _STOP_RUN_FAILED, second
        assert second["started_run_id"] is None
        assert "state=FAILED" in second["decision"]["cited_facts"], (
            "失败面必须点名终态（不笼统「没继续」）",
            second,
        )
        assert "未获结论" in second["decision"]["reason"], second["decision"]["reason"]
        assert read_program(client, _program_id(program))["run_count"] == 1


def test_a_verdict_that_misses_the_rule_stops_the_program_by_conclusion() -> None:
    """`STOP_RULE`（**结论面**）：那一轮**跑成**（`SUCCEEDED`）但落库判词不命中续跑规则
    ⇒ 按结论停，且判词**逐字**进 `cited_facts`（不笼统「评审不通过」）。

    **为什么这条在树**（GOAL-20261009-041 纪律回溯修复）：本用例是**回补**——
    GOAL-20261008-040 把原先那条 `STOP_RULE` 用例改成失败面断言时，结论面在 e2e 上
    **失去了覆盖**（新增的 `test_program_stop_reasons_are_decidable.py` 只有否定式
    「空 `cited_facts` 不得出现」，没有一条真跑出 `STOP_RULE` 的用例；驱动单元判据里
    那条用的 `_Harness` 是**假终态**路径，不经 HTTP 面）。本形态**可构造**且**必须**被覆盖：
    把 `continue_on` 声明成**不命中**上一轮判词的值即可（实测：`SUCCEEDED` +
    `verdict PASS` + `want=['ACCEPT']` ⇒ `STOP_RULE`）。
    **与失败面的分界**（本用例断言两件事同时成立）：种类是 `STOP_RULE`（不是
    `STOP_RUN_FAILED`）、**且**那一轮终态是 `SUCCEEDED` —— 后者保证它不是靠失败面
    蒙对的（受判面非空、两向可分）。
    """
    with TestClient(create_app(program_deps())) as client:
        program = create_program(client, max_runs=3, continue_on=["ACCEPT"])
        advance(client, _program_id(program))
        second = advance(client, _program_id(program))
        assert second["decision"]["kind"] == _STOP_RULE, second
        assert second["decision"]["kind"] != _STOP_RUN_FAILED
        assert second["started_run_id"] is None
        assert second["decision"]["cited_facts"] == ["verdict PASS"], (
            "落库判词必须**逐字**进决策（不笼统「评审不通过」）",
            second,
        )
        detail = read_program(client, _program_id(program))
        assert detail["run_count"] == 1
        assert [row["state"] for row in detail["runs"]] == ["SUCCEEDED"], (
            "结论面停的前提是**这一轮跑成了**；失败轮走失败面（那条由上一个用例覆盖）",
            detail["runs"],
        )


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


def test_a_declared_gate_stops_the_http_advance_and_the_read_face_shows_it() -> None:
    """GOAL-20261010-046 EC-04(a)：经**既有 HTTP 面**声明的闸门 ⇒ 该轮跑完后的推进停下等人。

    与驱动单元判据（`test_program_waiting_on_the_run_path.py`）的分工：那条判**判定值**；
    本条判**产品路径真的接上了** —— 建程序时声明 `human_gate_at_index=1`，第 1 轮跑完
    （`SUCCEEDED`，判词 `PASS` 本可续跑）后的推进必须落 `WAIT_FOR_APPROVAL` 且**点名**
    声明值，**不**起第 2 轮；读面把声明回显出来。
    """
    with TestClient(create_app(program_deps())) as client:
        program = create_program(client, max_runs=3, human_gate_at_index=1)
        assert program["human_gate_at_index"] == 1, ("建程序回执必须回显声明", program)
        first = advance(client, _program_id(program))
        assert first["decision"]["kind"] == _START, first
        assert first["started_run_id"], first
        second = advance(client, _program_id(program))
        assert second["decision"]["kind"] == _WAIT_FOR_APPROVAL, second
        assert second["decision"]["kind"] != _CONTINUE, (
            "闸门必须**先于**结论面拦住（否则声明了闸门却照常续跑）",
            second,
        )
        assert "human_gate_at_index=1" in second["decision"]["reason"], second["decision"]
        assert "人工闸门" in second["decision"]["reason"], second["decision"]
        assert second["started_run_id"] is None, "等人拍板时不得起新轮"
        detail = read_program(client, _program_id(program))
        assert detail["human_gate_at_index"] == 1, ("读面必须披露声明", detail)
        assert detail["run_count"] == 1, "第 2 轮不得被起（闸门拦住）"


def test_an_undeclared_gate_leaves_the_http_advance_unchanged() -> None:
    """GOAL-20261010-046 EC-04 反证臂②：**未声明** ⇒ 同一实跑逐字走结论面（`CONTINUE`）。

    与上一条配对（同一协议 / 同一实跑装配）：唯一差别是**不发** `human_gate_at_index`。
    两轮都照常起，第 2 次推进落 `CONTINUE` 且被引事实只有**判词**（没有闸门字样）
    —— 这是「缺省 ⇒ 既有行为逐字不变」在**产品路径**上的证据。
    """
    with TestClient(create_app(program_deps())) as client:
        program = create_program(client, max_runs=3)
        assert program["human_gate_at_index"] is None, ("未声明必须读面为 None", program)
        first = advance(client, _program_id(program))
        assert first["decision"]["kind"] == _START, first
        second = advance(client, _program_id(program))
        assert second["decision"]["kind"] == _CONTINUE, second
        assert second["decision"]["cited_facts"] == ["verdict PASS"], second["decision"]
        assert second["started_run_id"], second
        assert read_program(client, _program_id(program))["run_count"] == 2, "缺省路径照常续跑"


def test_a_declared_gate_can_be_decided_and_the_program_resumes() -> None:
    """GOAL-20261010-047 EC-03：声明的闸门**接得回** —— 经既有审批面裁决后推进照常继续。

    **本轮的靶子**（此前实测「只停不回」）：闸门拦住后，`GET /runs/{id}/approvals`
    返回**空**、`run_count` 恒 1，程序**永远**停在那一轮。本用例把**整条回路**走完：
    闸门拦住 → 产品面上**有**一条待决（点名在判词里）→ 经 `POST /approvals/{id}/decide`
    裁决 → 再推进**照常续**（`CONTINUE`）。**该轮不重跑**（第 1 轮仍只有一条 run）。
    """
    with TestClient(create_app(program_deps())) as client:
        program = create_program(client, max_runs=3, human_gate_at_index=1)
        pid = _program_id(program)
        first = advance(client, pid)
        run_id = first["started_run_id"]
        assert run_id, first

        second = advance(client, pid)
        assert second["decision"]["kind"] == _WAIT_FOR_APPROVAL, second
        named = [f for f in second["decision"]["cited_facts"] if f.startswith("approval_id=")]
        assert named, ("判词必须点名注册到的审批标识", second["decision"])

        listing = client.get(f"/runs/{run_id}/approvals")
        assert listing.status_code == 200, listing.text
        rows = listing.json()
        assert len(rows) == 1, ("声明闸门必须在既有审批面上注册**一条**待决", rows)
        assert rows[0]["status"] == "PENDING", rows
        assert rows[0]["risk"] == "HUMAN_GATE", rows
        approval_id = rows[0]["id"]

        # 幂等：再推一次不新增待决（否则「等人拍板」堆成一串）
        advance(client, pid)
        assert len(client.get(f"/runs/{run_id}/approvals").json()) == 1, "重复推进不得堆积"

        decided = client.post(
            f"/approvals/{approval_id}/decide",
            json={"decision": "approve"},
            headers={"If-Match": "*", "Idempotency-Key": "goal047-decide"},
        )
        assert decided.status_code == 200, decided.text
        assert decided.json()["status"] == "APPROVED", decided.json()

        third = advance(client, pid)
        assert third["decision"]["kind"] == _CONTINUE, ("裁决后必须照常续", third)
        assert third["started_run_id"], third
        detail = read_program(client, pid)
        assert detail["run_count"] == 2, ("第 1 轮不得重跑；续跑落在该轮**之后**", detail)
        assert [row["program_index"] for row in detail["runs"]] == [1, 2], detail["runs"]


def test_a_conditional_gate_fires_on_the_landed_verdicts_over_the_http_face() -> None:
    """GOAL-20261010-048 EC-03：**条件式**闸门经**既有 HTTP 面**成立 —— 按落库事实触发。

    与序号闸门（序 14）的分工：那条按**轮次**拦，本条按**落库判词取值**拦。
    配对的**反证臂**是下一条（条件不命中 ⇒ 逐字走结论面）。
    """
    with TestClient(create_app(program_deps())) as client:
        program = create_program(client, max_runs=3, human_gate_on_verdicts=["PASS"])
        pid = _program_id(program)
        assert program["human_gate_on_verdicts"] == ["PASS"], ("读面必须回显声明", program)
        first = advance(client, pid)
        assert first["decision"]["kind"] == _START, first
        second = advance(client, pid)
        assert second["decision"]["kind"] == _WAIT_FOR_APPROVAL, second
        facts = second["decision"]["cited_facts"]
        assert "human_gate_on_verdicts=['PASS']" in facts, ("必须点名声明的条件", facts)
        assert "verdict PASS" in facts, ("必须点名命中它的**落库事实**", facts)
        assert second["started_run_id"] is None, "条件命中时不得起下一轮"
        assert read_program(client, pid)["run_count"] == 1


def test_a_conditional_gate_that_is_not_hit_leaves_the_advance_unchanged() -> None:
    """**反证臂**：声明的条件**不命中**落库判词 ⇒ 逐字走结论面（`CONTINUE`），不注册、不停。

    与上一条**配对**（同一协议 / 同一实跑装配）：唯一差别是**声明的取值**。
    """
    with TestClient(create_app(program_deps())) as client:
        program = create_program(client, max_runs=3, human_gate_on_verdicts=["REJECT"])
        pid = _program_id(program)
        first = advance(client, pid)
        assert first["decision"]["kind"] == _START, first
        second = advance(client, pid)
        assert second["decision"]["kind"] == _CONTINUE, second
        assert second["decision"]["cited_facts"] == ["verdict PASS"], second["decision"]
        assert second["started_run_id"], second
        detail = read_program(client, pid)
        assert detail["run_count"] == 2, ("条件不命中 ⇒ 照常续跑", detail)


def test_an_undecided_gate_still_stops_the_program() -> None:
    """GOAL-20261010-047 反证臂：**未裁决** ⇒ 仍停（注册了待决**不等于**放行）。"""
    with TestClient(create_app(program_deps())) as client:
        program = create_program(client, max_runs=3, human_gate_at_index=1)
        pid = _program_id(program)
        advance(client, pid)
        for _ in range(2):
            result = advance(client, pid)
            assert result["decision"]["kind"] == _WAIT_FOR_APPROVAL, result
            assert result["started_run_id"] is None, "人没拍板不得起下一轮"
        assert read_program(client, pid)["run_count"] == 1
