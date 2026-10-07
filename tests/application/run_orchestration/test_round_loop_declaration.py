"""GOAL-20261008-034 EC-01/EC-02 判据（纯逻辑面）：多轮循环的**声明面**与**停止判据**。

本文件只判两个新模块的**纯函数**（展开 / 反查 / 取事实 / 停止判定）——不跑编排。
**编排面的判据**（三轮真的跑起来、派生可追、两臂可区分）在 e2e 文件里，两者互补。

**为什么先有这一层**：停止规则的**顺序**（先判结论、再判护栏）与**类别**（`CONCLUSION`
vs `MAX_ROUNDS`）是 EC-02 的核心 —— 它们必须在**纯函数**层面就被钉住，否则 e2e 里的
「哪一臂停的」会被编排噪音淹没（例如「刚好跑到上界且结论也收敛了」这种重叠情形）。
"""

from __future__ import annotations

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
    ids_from_step_outputs,
)

_LOOP = RoundLoop(phases=("round",), max_rounds=4)


class TestTheDeclarationFace:
    def test_expansion_keeps_the_first_round_id_untouched(self) -> None:
        """**第 1 轮用原始 id** —— 既有单轮语义逐字不动（展开只在 N>1 时加后缀）。"""
        assert RoundLoop(phases=("a", "b"), max_rounds=3).expanded_phases() == (
            "a",
            "b",
            "a@2",
            "b@2",
            "a@3",
            "b@3",
        )

    def test_expansion_produces_distinct_ids_per_round(self) -> None:
        """**每轮 id 必须不同**：任务 idempotency key 由 `{run}:{phase}:{agent}` 派生，
        同 id ⇒ 第二轮 submit 被既有按 key 去重吞掉 ⇒ **静默停**（最危险的失败形态）。"""
        expanded = RoundLoop(phases=("round",), max_rounds=3).expanded_phases()
        assert len(set(expanded)) == len(expanded) == 3

    def test_a_single_round_loop_is_refused(self) -> None:
        """一轮的「循环」不是循环 ⇒ 构造期点名拒绝。"""
        with pytest.raises(ValueError, match="not a loop"):
            RoundLoop(phases=("a",), max_rounds=1)

    def test_an_unknown_stop_criterion_is_refused_by_name(self) -> None:
        with pytest.raises(ValueError, match="unknown stop criterion"):
            RoundLoop(phases=("a",), max_rounds=2, stop_when="whatever")

    def test_find_loop_resolves_both_the_plain_and_the_expanded_id(self) -> None:
        """反查必须**剥后缀**：第 2 轮用的是 `round@2`，不剥就认不出来。"""
        assert find_loop((_LOOP,), "round") == (_LOOP, 1)
        assert find_loop((_LOOP,), "round@3") == (_LOOP, 3)
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
        outputs = (
            {"content": {"ids": ["39000001", "39000002"]}, "artifact_id": "x"},
            {"content": {"title": "no ids here"}},
            {"no_content": True},
        )
        assert ids_from_step_outputs(outputs) == ("39000001", "39000002")

    def test_the_reading_is_deduplicated_and_order_preserving(self) -> None:
        outputs = ({"content": {"ids": ["a", "b"]}}, {"content": {"ids": ["b", "c"]}})
        assert ids_from_step_outputs(outputs) == ("a", "b", "c")

    def test_a_round_with_no_id_typed_output_reads_as_empty(self) -> None:
        """整轮没有标识型产出 ⇒ 空元组 ⇒ 判据判「无新标识」⇒ 停（语义：这轮没带来新东西）。"""
        assert ids_from_step_outputs(({"content": {"note": "x"}},)) == ()
        assert ids_from_step_outputs(()) == ()

    def test_new_ids_is_a_set_difference_not_a_count(self) -> None:
        """「新」是**集合差**：同一批标识重来一遍**不算新**（计数相同会误判成「有进展」）。"""
        fact = RoundFact(round_index=3, ids=("a", "b"), seen_before=("b", "a"))
        assert fact.new_ids == ()
