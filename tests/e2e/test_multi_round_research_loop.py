"""E2E（GOAL-20261008-034 EC-01/EC-02）：**三轮研究循环 + 结论驱动的停止**。

**它补的是什么**（建档实测的三条）：① `ITERATIVE_OPTIMIZER` / `POPULATION_SEARCH` 是枚举
孤儿（三个执行面零消费）；② `stop_conditions` 解析 / 编译 / preflight 三段落都有、
**运行期零消费** ⇒ `max_iterations: 4` 是装饰性声明；③ 相位执行链是**单遍**拓扑序 ⇒
今天的「多轮」只能靠在协议里写死多个 phase（= MAINLINE 明文列为「不算推进深度轴」）。

本文件判**真的多轮**：同一组 phase 按 `RoundLoop` 声明**重复执行到停**，
停止判据读**本轮结论的可观察事实**。

四件事（(a) 声明 / (b) 三轮 / (c) 停止可区分 / (d) 反证）：

1. **(a) 循环是声明的**：`RoundLoop`（相序列 / `max_rounds` / 判据名 / 每轮调用）逐条
   钉在判据里 —— 应用层没有「如果就」。
2. **(b) 三轮真的跑**：三轮各返回**新**标识 ⇒ 循环继续到上界 ⇒ 三个任务、三次检索。
3. **(c) 停止可区分**：**护栏臂**（每轮有新标识）⇒ `MAX_ROUNDS`；**结论臂**（某轮无新
   标识）⇒ `CONCLUSION`。两臂**互斥**。
4. **(d) 反证**：把上界的护栏**去掉**（`max_rounds` 拉到远超实际轮数）⇒ 结论臂的停止
   理由必须仍是**结论**（说明停不是被上界逼出来的）；护栏臂则**跑满**新上界。

**如实边界**：本文件**不**声称「模型读懂了上一轮」（交付物契约只判产物存在与来源覆盖）；
**不**声称三轮之后已收敛（收敛是判据的结论，不是本文件的断言）。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from fastapi.testclient import TestClient

from packages.application.run_orchestration.round_loop import (
    STOP_BY_CONCLUSION,
    STOP_BY_GUARD,
    RoundLoop,
)
from packages.application.run_orchestration.round_loop_runner import round_specs
from packages.application.run_orchestration.service import RunOrchestrationService
from services.api.app import create_app
from tests.e2e.live_run_support import start_run as _start
from tests.e2e.multi_round_loop_support import (
    LOOPED_PHASE,
    QUERIES,
    ROUND_PMIDS,
    RoundsOfflineNcbi,
    deps_with_loop,
    looped_calls,
)
from tests.e2e.test_ec03_real_runtime_offline_chain import _read_chain, mock_relay
from tests.e2e.two_round_loop_support import PROTOCOL, TOOL_IDS, phase_of_task

__all__ = ["mock_relay"]


def _run(mock_relay_url: str, *, max_rounds: int = 3, query_for: Any = None) -> dict[str, Any]:
    """跑一次多轮 run 并取回读面 + 事件链快照（`query_for` 可换某一轮的检索词）。"""
    offline = RoundsOfflineNcbi()
    deps = deps_with_loop(mock_relay_url, offline=offline, max_rounds=max_rounds)
    if query_for is not None:
        service = deps.runs
        base = service._deps
        loop = base.round_loops[0]
        calls = tuple(
            _swap_query(looped_calls(index), query_for[index])
            if index in query_for
            else looped_calls(index)
            for index in range(1, max_rounds + 1)
        )
        deps = replace(
            deps,
            runs=RunOrchestrationService(
                replace(base, round_loops=(replace(loop, calls_by_round=calls),))
            ),
        )
    with TestClient(create_app(deps)) as client:
        run = _start(client, PROTOCOL)
        reads = _read_chain(client, run)  # 经**既有读面**取事实（判据才与 API 一致）
        events = client.get(f"/runs/{run['id']}/events").json()
    return {"run": run, "reads": reads, "offline": offline, "events": events}


def _swap_query(calls: tuple[Any, ...], query: str) -> tuple[Any, ...]:
    """把该轮检索调用的词换成给定值（其余逐字不动）——**反证 / 收敛臂的声明面**。"""
    search_call = TOOL_IDS["literature.search"]
    return tuple(
        replace(call, fixed_arguments={**dict(call.fixed_arguments), "query": query})
        if call.tool_id == search_call
        else call
        for call in calls
    )


def _rounds_fact(events: list[dict[str, Any]]) -> dict[str, Any]:
    """从事件链取**循环停止事实**（带 `rounds` 键的那条 `run.completed`）。

    为什么不是「第一条 `run.completed`」：跑过循环的 run 事件链里会有**两条**
    `run.completed` —— 一条带 `rounds`（循环收尾，本判据的受判面），一条不带
    （单遍执行的原样载荷，既有语义）。判据必须点名**带键的那条**；把「第一条」当
    受判面会在两者顺序变化时静默读到错的那条（**实测踩到**）。
    """
    for envelope in events:
        event = envelope.get("event") if isinstance(envelope, dict) else None
        if not isinstance(event, dict):
            event = envelope
        if str(event.get("type")) != "run.completed":
            continue
        payload = event.get("payload", {})
        fact = payload.get("rounds") if isinstance(payload, dict) else None
        if isinstance(fact, dict):
            return fact
    raise AssertionError(
        f"事件链里没有带 rounds 键的 run.completed（没跑循环？）：{[e.get('type') for e in events]}"
    )


class TestTheLoopIsDeclared:
    """(a) 循环是**声明**的：字段逐条在场，应用层没有「如果就」。"""

    def test_the_declaration_carries_every_decision(self) -> None:
        loop = RoundLoop(phases=(LOOPED_PHASE,), max_rounds=3)
        assert loop.phases == (LOOPED_PHASE,), "重复哪些 phase 是声明的"
        assert loop.max_rounds == 3, "最多几轮是声明的（护栏）"
        assert loop.stop_when == "converged_no_new_ids", "什么时候停是声明的（结论判据）"

    def test_each_round_declares_its_own_search_term(self) -> None:
        """**轮次差异由声明承担**：每轮检索词不同（否则第 2 轮就收敛，测不到三轮）。"""
        assert len(QUERIES) >= 3
        assert len(set(QUERIES)) == len(QUERIES), "每轮检索词必须不同"
        for left, right in zip(ROUND_PMIDS, ROUND_PMIDS[1:], strict=False):
            assert set(left).isdisjoint(right), "每轮必须返回**新**标识，否则测的是收敛不是多轮"

    def test_the_round_key_changes_but_the_phase_id_does_not(self) -> None:
        """**轮次改任务身份，不改 phase id**（两条都是实测发现的关键约束）。

        ① phase id 带轮次后缀 ⇒ 运行链的 phase 级过滤（拿它查编译计划表）查不到
        ⇒ 第 2 轮起**所有运行链调用被静默跳过**；
        ② 任务 id / 幂等键不带轮次 ⇒ 要么被既有按 key 去重**静默吞掉**，要么在
        同一条任务上以不同 digest 重登记同一 `source_ref` ⇒ 撞
        `conflicting source registration`（实测：第一轮成功、第二轮 FAILED）。
        """
        from packages.domain.core import ID
        from packages.domain.task_state import ResearchTaskState
        from packages.domain.tasks import ResearchTask

        loop = RoundLoop(phases=(LOOPED_PHASE,), max_rounds=3)
        task = ResearchTask(
            id=ID.generate(),
            run_id=ID.generate(),
            status=ResearchTaskState.State.QUEUED,
            contract_id="c",
            idempotency_key="run:round1:agent",
        )
        specs = ((task, "contract", None),)

        round_one = round_specs(loop, 1, specs)
        assert round_one[0][0].id == task.id, "第 1 轮逐字保留任务身份（既有语义不动）"
        assert round_one[0][0].idempotency_key == task.idempotency_key

        round_two = round_specs(loop, 2, specs)
        assert round_two[0][0].idempotency_key.endswith("@2"), round_two[0][0]
        assert round_two[0][0].id != task.id, "第 2 轮必须是**不同的任务**（否则撞 source 登记）"
        assert loop.round_key("k", 1) == "k", "第 1 轮的键逐字不同"


class TestThreeRoundsReallyRun:
    """(b) 三轮真的跑起来（每轮有新标识 ⇒ 循环继续到上界）。"""

    def test_three_rounds_run_and_the_guard_stops_it(self, mock_relay: str) -> None:
        fact = _rounds_fact(_run(mock_relay, max_rounds=3)["events"])
        assert fact["rounds_run"] == 3, f"必须跑满三轮（实测 {fact['rounds_run']}）"
        assert fact["stopped_by"] == STOP_BY_GUARD, (
            f"每轮都有新标识 ⇒ 只能由上界停（实测 {fact['stopped_by']}）"
        )
        assert fact["criterion"] == "max_rounds"
        assert fact["new_ids_this_round"], "护栏停时本轮**有**新标识（否则该读成结论停）"

    def test_every_round_searches_with_its_own_term(self, mock_relay: str) -> None:
        """**每轮真的检索过**（离线传输层逐轮收到该轮的词）。

        这是「每轮**是不同的任务**」的可观察后果：若轮次没改幂等键，第二轮的提交会被
        既有按 key 去重**静默吞掉** ⇒ 这里只会看到一次检索（而**不是**报错）。
        """
        payload = _run(mock_relay, max_rounds=3)
        searches = [q for endpoint, q in payload["offline"].requests if endpoint == "esearch.fcgi"]
        assert len(searches) >= 3, f"三轮各检索一次（实测 {len(searches)}）"
        for query in QUERIES[:3]:
            assert any(query in item for item in searches), f"缺第 {query} 轮（{searches}）"

    def test_the_rounds_are_visible_as_separate_tasks(self, mock_relay: str) -> None:
        """三轮在任务面**可数**（同一 phase 三个任务，不是同一个跑了三次）。"""
        reads = _run(mock_relay, max_rounds=3)["reads"]
        looped = [t for t, phase in phase_of_task(reads).items() if phase == LOOPED_PHASE]
        assert len(looped) >= 3, f"同一 phase 至少三个任务（实测 {len(looped)}）"


class TestTheStopIsConclusionDriven:
    """(c)(d) 停止**可区分**：结论驱动 vs 上界护栏，两臂互斥。"""

    def test_a_converging_loop_stops_by_conclusion_even_with_a_far_guard(
        self, mock_relay: str
    ) -> None:
        """**结论臂 + 反证**：让第 2 轮**零命中**（检索词不在离线表里 ⇒ 回落到旧标识集）
        并把上界拉到 **9** ⇒ 停止理由必须仍是 **`CONCLUSION`**（不是被上界逼停），
        且 `rounds_run=2`。

        这条同时是 (d) 的反证形态：把上界抬到远超实际轮数，就能把「结论驱动的停」
        与「上界逼停」**分开读** —— 判据若失效（例如停止判据不生效），`rounds_run`
        会变成 9 而不是 2 ⇒ 判红。
        """
        payload = _run(mock_relay, max_rounds=9, query_for={2: "zero-hit-round-two"})
        fact = _rounds_fact(payload["events"])
        assert fact["rounds_run"] == 2, (
            f"第 2 轮零命中 ⇒ 无新标识 ⇒ 必须停在 2（实测 {fact['rounds_run']}）"
        )
        assert fact["stopped_by"] == STOP_BY_CONCLUSION, (
            f"结论已收敛时必须读成结论停（实测 {fact['stopped_by']}）"
        )
        assert fact["criterion"] == "converged_no_new_ids"
        assert fact["new_ids_this_round"] == [], "结论停的读数是「本轮新标识为空」"
        assert fact["max_rounds"] == 9, "上界远大于实际轮数 ⇒ 停不是上界逼的"

    def test_the_conclusion_wins_when_it_coincides_with_the_guard(self, mock_relay: str) -> None:
        """**顺序的判据**：结论收敛与上界同时成立 ⇒ 必须读成 `CONCLUSION`。

        构造：上界 = 2，并且第 2 轮零命中（两者同时成立）。若判据顺序反了（先判护栏），
        这里会读成 `MAX_ROUNDS` ⇒ 「已经收敛」被谎报成「只是上界到了」—— 正是
        MAINLINE 禁止的「把结论驱动谎报成固定轮数」。
        """
        fact = _rounds_fact(
            _run(mock_relay, max_rounds=2, query_for={2: "zero-hit-round-two"})["events"]
        )
        assert fact["rounds_run"] == 2
        assert fact["stopped_by"] == STOP_BY_CONCLUSION, (
            "结论收敛时必须读成结论停，即使同时到达上界"
        )

    def test_the_two_stop_kinds_are_mutually_exclusive(self, mock_relay: str) -> None:
        """两臂**互斥**：同一读数不可能同时是「结论停」与「护栏停」。"""
        guard = _rounds_fact(_run(mock_relay, max_rounds=3)["events"])
        conclusion = _rounds_fact(
            _run(mock_relay, max_rounds=9, query_for={2: "zero-hit-round-two"})["events"]
        )
        assert guard["stopped_by"] == STOP_BY_GUARD
        assert conclusion["stopped_by"] == STOP_BY_CONCLUSION
        assert guard["stopped_by"] != conclusion["stopped_by"]
        assert guard["new_ids_this_round"] != conclusion["new_ids_this_round"]


class TestStopAndSkipAreVisibleOnTheReadFace:
    """EC-03：停止与跳过都落在**既有读面**（可观测，非静默）。"""

    def test_the_stop_fact_is_readable_from_the_event_stream(self, mock_relay: str) -> None:
        """停止事实（判据 / 类别 / 读数 / 轮数）经**既有事件读面**可逐字读出。"""
        payload = _run(mock_relay, max_rounds=3)
        fact = _rounds_fact(payload["events"])
        for key in ("rounds_run", "stopped_by", "criterion", "max_rounds", "ids_seen"):
            assert key in fact, f"停止读面缺 {key}：{sorted(fact)}"
        assert fact["stopped_by"] in {STOP_BY_CONCLUSION, STOP_BY_GUARD}

    def test_a_converged_round_reports_the_empty_reading_not_a_silent_stop(
        self, mock_relay: str
    ) -> None:
        """结论停必须**说清读到了什么**（`new_ids_this_round == []`）——停不是静默。"""
        fact = _rounds_fact(
            _run(mock_relay, max_rounds=9, query_for={2: "zero-hit-round-two"})["events"]
        )
        assert fact["stopped_by"] == STOP_BY_CONCLUSION
        assert fact["new_ids_this_round"] == [], "停的理由必须可复读（本轮新标识为空）"
        assert fact["ids_seen"], "累计标识仍在读面上（可核「之前确实有东西」）"


class TestTheSinglePassPathIsUnchanged:
    """**既有语义不因本轮扩张而漂移**：没声明循环的 run 载荷逐字不变。"""

    def test_a_run_without_a_loop_emits_no_rounds_key(self, mock_relay: str) -> None:
        """未声明 `round_loops` ⇒ `run.completed` **不带** `rounds` 键（既有载荷逐字不变）。

        反证形态：本判据取的是**单遍路径**（两轮协议夹具，无循环声明）⇒ 若循环载荷
        被无条件写入，这里会看到多余的键。
        """
        from tests.e2e.multi_round_loop_support import RoundsOfflineNcbi as _Offline
        from tests.e2e.two_round_loop_support import assembled_deps

        offline = _Offline()
        deps = assembled_deps(mock_relay, offline=offline)  # type: ignore[arg-type]
        with TestClient(create_app(deps)) as client:
            run = _start(client, PROTOCOL)
            events = client.get(f"/runs/{run['id']}/events").json()
        completed = [
            (e.get("event") or e)
            for e in events
            if str((e.get("event") or e).get("type")) == "run.completed"
        ]
        assert completed, "单遍路径必须发 run.completed"
        assert all("rounds" not in (item.get("payload") or {}) for item in completed), (
            "没跑循环的 run 不得带 rounds 键（既有载荷逐字不变）"
        )

    def test_the_round_payload_keeps_the_single_pass_keys(self, mock_relay: str) -> None:
        """跑循环时，`run.completed` 仍带单遍那些键（`run_id`，以及有跳过时的 `skipped`）。

        这条防的是我在实现里发现的**真缺口**：循环收尾若只发 `{run_id, rounds}`，
        就会把该轮的**声明式跳过事实**丢掉 —— 那正是 EC-03 禁止的静默。
        """
        payload = _run(mock_relay, max_rounds=3)
        completed = [
            (e.get("event") or e)
            for e in payload["events"]
            if str((e.get("event") or e).get("type")) == "run.completed"
        ]
        with_rounds = [
            c for c in completed if isinstance((c.get("payload") or {}).get("rounds"), dict)
        ]
        assert with_rounds, "跑过循环的 run 必须有一条带 rounds 的 run.completed"
        for item in with_rounds:
            body = item.get("payload") or {}
            assert body.get("run_id"), "循环载荷仍带 run_id（单遍同形）"


class TestAConvergedRoundIsNotSilent:
    """EC-03：结论停的那一轮，**读到什么**必须可复读（不是静默停）。"""

    def test_a_zero_hit_round_names_the_empty_reading_it_stopped_on(self, mock_relay: str) -> None:
        """**零命中轮** ⇒ 该轮 `new_ids_this_round == []` 且 `ids_seen` 仍是**之前累计**的。

        这两条合起来就是「停的理由可复读」：既说清**这一轮没带来新东西**，也保留
        **之前确实有东西**（否则「空」无法与「从来没有过」区分）。

        **如实边界**：本夹具的零命中轮里，**检索步本身**返回空 idlist ⇒ 读取步的
        「带理由跳过」（`requires_previous_ids=False`）在该路径上**不会触发** ——
        那一支由两轮协议族的既有判据覆盖（`test_research_loop_second_round_derived.py`）。
        本判据**只**判循环收尾的读数（那是本轮新增的面）。
        """
        from tests.e2e.multi_round_loop_support import ZERO_HIT_QUERY

        payload = _run(mock_relay, max_rounds=2, query_for={2: ZERO_HIT_QUERY})
        fact = _rounds_fact(payload["events"])

        assert fact["stopped_by"] == STOP_BY_CONCLUSION
        assert fact["new_ids_this_round"] == [], "这一轮没带来新标识（停的依据）"
        assert fact["ids_seen"] == list(ROUND_PMIDS[0]), (
            f"累计标识仍是第一轮的（实测 {fact['ids_seen']}）—— 「空」必须能与「从未有过」区分"
        )
        assert fact["rounds_run"] == 2

    def test_the_loop_payload_still_carries_the_single_pass_keys(self, mock_relay: str) -> None:
        """循环载荷与单遍**同形**：`run_id` 在位（`skipped` 键按既有口径只在有跳过时出现）。

        实现里发现过的真缺口：循环收尾若只发 `{run_id, rounds}`，该轮的跳过事实会**丢**。
        本条钉住「单遍键被保留」这一形态（跳过键的**存在性**由两轮协议族的既有判据覆盖——
        本夹具的零命中路径不触发读取步跳过，故不在此断言）。
        """
        payload = _run(mock_relay, max_rounds=3)
        with_rounds = [
            (e.get("event") or e)
            for e in payload["events"]
            if str((e.get("event") or e).get("type")) == "run.completed"
            and isinstance(((e.get("event") or e).get("payload") or {}).get("rounds"), dict)
        ]
        assert with_rounds
        for item in with_rounds:
            body = item.get("payload") or {}
            assert body.get("run_id"), "循环载荷仍带 run_id（与单遍同形）"
            assert "rounds" in body
