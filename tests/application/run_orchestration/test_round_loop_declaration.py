"""GOAL-20261008-034 EC-01/EC-02 判据（纯逻辑面）：多轮循环的**声明面**与**停止判据**。

本文件只判两个新模块的**纯函数**（展开 / 反查 / 取事实 / 停止判定）——不跑编排。
**编排面的判据**（三轮真的跑起来、派生可追、两臂可区分）在 e2e 文件里，两者互补。

**为什么先有这一层**：停止规则的**顺序**（先判结论、再判护栏）与**类别**（`CONCLUSION`
vs `MAX_ROUNDS`）是 EC-02 的核心 —— 它们必须在**纯函数**层面就被钉住，否则 e2e 里的
「哪一臂停的」会被编排噪音淹没（例如「刚好跑到上界且结论也收敛了」这种重叠情形）。
"""

from __future__ import annotations

from typing import Any

import pytest

from packages.application.run_orchestration.round_loop import (
    CONVERGED_NO_NEW_IDS,
    STOP_BY_CONCLUSION,
    STOP_BY_GUARD,
    RoundLoop,
    find_loop,
)
from packages.application.run_orchestration.round_loop_facts import (
    RoundFact,
    evaluate_stop,
    ids_at_path,
    ids_from_step_outputs,
)

_LOOP = RoundLoop(phases=("round",), max_rounds=4)


class TestTheDeclarationFace:
    def test_round_one_keeps_the_base_key_untouched(self) -> None:
        """**第 1 轮用基键逐字不变** —— 既有单轮语义与「续跑按幂等键对齐」逐字不动。"""
        loop = RoundLoop(phases=("a", "b"), max_rounds=3)
        assert loop.round_key("run:a:agent", 1) == "run:a:agent"

    def test_later_rounds_get_distinct_keys(self) -> None:
        """**每轮键必须不同**：幂等键由 `{run}:{phase}:{agent}` 派生，同键 ⇒ 第二轮
        submit 被既有按 key 去重吞掉 ⇒ **静默停**（最危险的失败形态）。"""
        loop = RoundLoop(phases=("round",), max_rounds=3)
        keys = {loop.round_key("run:round:agent", index) for index in (1, 2, 3)}
        assert len(keys) == 3
        assert "run:round:agent@2" in keys and "run:round:agent@3" in keys

    def test_the_phase_id_itself_is_never_suffixed(self) -> None:
        """**phase id 不带轮次后缀**（实测发现的关键约束）：运行链的 phase 级过滤
        （`planned_in_this_phase`）拿 spec 的 phase id 去编译计划里查表 —— 带后缀就查不到
        ⇒ 第 2 轮起**所有运行链调用被静默跳过**（不是报错，是安静地什么都不做）。"""
        loop = RoundLoop(phases=("round",), max_rounds=3)
        assert not hasattr(loop, "round_phase_id"), "phase id 不得有展开形态"
        assert not hasattr(loop, "expanded_phases"), "不得提供整体展开（会让停止判据变成装饰）"

    def test_a_single_round_loop_is_refused(self) -> None:
        """一轮的「循环」不是循环 ⇒ 构造期点名拒绝。"""
        with pytest.raises(ValueError, match="not a loop"):
            RoundLoop(phases=("a",), max_rounds=1)

    def test_an_unknown_stop_criterion_is_refused_by_name(self) -> None:
        with pytest.raises(ValueError, match="unknown stop criterion"):
            RoundLoop(phases=("a",), max_rounds=2, stop_when="whatever")

    def test_find_loop_resolves_the_plain_phase_id_every_round(self) -> None:
        """反查用**原始 phase id**（它是每轮同一个）——不是展开后的字符串。"""
        assert find_loop((_LOOP,), "round") is _LOOP
        assert find_loop((_LOOP,), "other") is None


class TestTheStopDecision:
    def test_new_ids_do_not_stop(self) -> None:
        decision = evaluate_stop(
            criterion=CONVERGED_NO_NEW_IDS,
            fact=RoundFact(round_index=1, ids=("a",), seen_before=()),
            round_index=1,
            max_rounds=4,
        )
        assert decision.stop is False
        assert decision.fact.new_ids == ("a",)

    def test_no_new_ids_stops_by_conclusion(self) -> None:
        decision = evaluate_stop(
            criterion=CONVERGED_NO_NEW_IDS,
            fact=RoundFact(round_index=2, ids=("a",), seen_before=("a",)),
            round_index=2,
            max_rounds=4,
        )
        assert decision.stop is True
        assert decision.kind == STOP_BY_CONCLUSION
        assert decision.criterion == CONVERGED_NO_NEW_IDS

    def test_the_guard_stops_when_the_conclusion_never_converges(self) -> None:
        decision = evaluate_stop(
            criterion=CONVERGED_NO_NEW_IDS,
            fact=RoundFact(round_index=4, ids=("d",), seen_before=("a", "b", "c")),
            round_index=4,
            max_rounds=4,
        )
        assert decision.stop is True
        assert decision.kind == STOP_BY_GUARD
        assert decision.criterion == "max_rounds"

    def test_the_conclusion_wins_when_both_would_stop(self) -> None:
        """**顺序的判据**（EC-02 (c) 的核心）：结论与护栏同时成立时，**必须**读成
        `CONCLUSION`。反过来（先判护栏）会把「结论已经收敛」谎报成「只是上界到了」——
        那是**把结论驱动谎报成固定轮数**，正是 MAINLINE 禁止的形态。"""
        decision = evaluate_stop(
            criterion=CONVERGED_NO_NEW_IDS,
            fact=RoundFact(round_index=4, ids=("a",), seen_before=("a",)),
            round_index=4,
            max_rounds=4,
        )
        assert decision.stop is True
        assert decision.kind == STOP_BY_CONCLUSION, (
            "结论收敛时，即使同时到达上界，停止理由也必须是 CONCLUSION"
        )

    def test_the_two_stop_kinds_are_distinguishable_on_the_same_reading(self) -> None:
        """**两臂互斥**（e2e 的纯函数形态）：同一读数下，新 ids 的有无**唯一**决定类别。"""
        converged = evaluate_stop(
            criterion=CONVERGED_NO_NEW_IDS,
            fact=RoundFact(round_index=2, ids=("a",), seen_before=("a",)),
            round_index=2,
            max_rounds=9,
        )
        still_new = evaluate_stop(
            criterion=CONVERGED_NO_NEW_IDS,
            fact=RoundFact(round_index=2, ids=("b",), seen_before=("a",)),
            round_index=2,
            max_rounds=9,
        )
        assert (converged.kind, still_new.kind, still_new.stop) == (
            STOP_BY_CONCLUSION,
            "",
            False,
        )


class TestTheFactReader:
    def test_ids_are_taken_from_the_declared_path(self) -> None:
        """两条**真实产出形态**各按自己的声明路径取：检索型 `ids`、读面型 `content.ids`。"""
        search = {"count": 2, "ids": ["39000001", "39000002"], "query": "x"}
        read = {"artifact_id": "a", "content": {"ids": ["39000001"]}}
        assert ids_at_path(search, "ids") == ("39000001", "39000002")
        assert ids_at_path(read, "content.ids") == ("39000001",)

    def test_a_missing_path_reads_as_empty_not_an_error(self) -> None:
        """取不到路径 ⇒ 空（该产出不是标识型）——**不是**错误、不是点名拒绝。"""
        assert ids_at_path({"articles": []}, "ids") == ()
        assert ids_at_path({"content": {"title": "x"}}, "content.ids") == ()
        assert ids_at_path({"content": "not-a-mapping"}, "content.ids") == ()

    def test_the_reading_is_deduplicated_and_order_preserving(self) -> None:
        outputs = ({"ids": ["a", "b"]}, {"ids": ["b", "c"]})
        assert ids_from_step_outputs(outputs, "ids") == ("a", "b", "c")

    def test_a_round_with_no_id_typed_output_reads_as_empty(self) -> None:
        """整轮没有标识型产出 ⇒ 空元组 ⇒ 判据判「无新标识」⇒ 停（语义：这轮没带来新东西）。"""
        assert ids_from_step_outputs(({"note": "x"},), "ids") == ()
        assert ids_from_step_outputs((), "ids") == ()

    def test_new_ids_is_a_set_difference_not_a_count(self) -> None:
        """「新」是**集合差**：同一批标识重来一遍**不算新**（计数相同会误判成「有进展」）。"""
        fact = RoundFact(round_index=3, ids=("a", "b"), seen_before=("b", "a"))
        assert fact.new_ids == ()


class TestTheLoopStateMachine:
    """执行面的循环控制状态机（AC-4）：逐轮记事实 → 判定 → 可复读的停止载荷。

    本类只判**状态机本身**（不跑编排）；「三轮真的跑起来」由 e2e 覆盖（AC-5）。
    """

    def _state(self, *, max_rounds: int = 4) -> Any:
        from packages.application.run_orchestration.round_loop_runner import RoundLoopState

        return RoundLoopState(loop=RoundLoop(phases=("round",), max_rounds=max_rounds))

    def test_new_ids_keep_the_loop_going(self) -> None:
        state = self._state()
        state.record_round(1, [{"ids": ["a"]}])
        decision = state.decide()
        assert decision.stop is False
        assert state.rounds_run == 1
        assert state.seen_ids == ("a",)

    def test_a_round_without_new_ids_stops_by_conclusion(self) -> None:
        state = self._state()
        state.record_round(1, [{"ids": ["a"]}])
        assert state.decide().stop is False
        state.record_round(2, [{"ids": ["a"]}])  # 同一批 ⇒ 无新
        decision = state.decide()
        assert decision.stop is True
        assert decision.kind == STOP_BY_CONCLUSION
        assert state.stopped_by == STOP_BY_CONCLUSION
        assert state.stop_criterion == CONVERGED_NO_NEW_IDS

    def test_the_guard_stops_a_never_converging_loop(self) -> None:
        state = self._state(max_rounds=3)
        for index in range(1, 4):
            state.record_round(index, [{"ids": [f"id{index}"]}])
            decision = state.decide()
        assert decision.stop is True
        assert decision.kind == STOP_BY_GUARD
        assert state.rounds_run == 3, "上界到点即停（不跑到第 4 轮）"

    def test_the_stop_payload_is_readable_and_names_the_criterion(self) -> None:
        """停止载荷必须**可复读**：判据名 / 类别 / 本轮新标识 / 累计标识 / 上界。"""
        state = self._state(max_rounds=2)
        state.record_round(1, [{"ids": ["a"]}])
        state.decide()
        state.record_round(2, [{"ids": ["a"]}])
        state.decide()
        payload = state.stop_payload()
        assert payload["rounds_run"] == 2
        assert payload["stopped_by"] == STOP_BY_CONCLUSION
        assert payload["criterion"] == CONVERGED_NO_NEW_IDS
        assert payload["new_ids_this_round"] == []
        assert payload["ids_seen"] == ["a"]
        assert payload["max_rounds"] == 2

    def test_the_state_refuses_to_report_before_it_actually_stopped(self) -> None:
        state = self._state()
        with pytest.raises(AssertionError):
            state.stop_payload()

    def test_validate_loops_names_an_unknown_phase(self) -> None:
        from packages.application.run_orchestration.round_loop_runner import validate_loops

        with pytest.raises(ValueError, match="unknown phases"):
            validate_loops((RoundLoop(phases=("ghost",), max_rounds=3),), ["real"])
        validate_loops((RoundLoop(phases=("real",), max_rounds=3),), ["real"])
