"""研究程序的域不变量（GOAL-20261008-037 EC-01）。

三件事各判一遍：

1. `ResearchRun` 的程序归属字段**同生同灭**（要么都有、要么都无），且序号 ≥ 1；
2. **逐字段复制**纪律：三个显式重建函数（`transition` / `with_manifest` /
   `with_protocol_source`）都必须带住程序字段 —— 漏一个就会在迁移一次后静默丢失归属
   （本仓既有教训的同一形状）；
3. `ResearchProgram` / `ProgramContinueRule` / `ProgramDecision` 的校验与**可区分**的
   决策种类（结论面与护栏面不共用同一种类）。
"""

from __future__ import annotations

import pytest

from packages.domain.core import ID
from packages.domain.program import (
    ProgramContinueRule,
    ProgramDecision,
    ProgramDecisionKind,
    ResearchProgram,
)
from packages.domain.run import ResearchRun

RUN_ID = "0f6a1f3a-6b1a-4a1e-9c3f-0d5f2b7c9e11"


def _run(**overrides: object) -> ResearchRun:
    base: dict[str, object] = {"id": ID(RUN_ID), "project_id": "p1", "protocol_id": "proto"}
    base.update(overrides)
    return ResearchRun(**base)  # type: ignore[arg-type]


def test_program_fields_are_all_or_nothing() -> None:
    with pytest.raises(ValueError, match="set together"):
        _run(program_id="prog-1")
    with pytest.raises(ValueError, match="set together"):
        _run(program_index=1)


def test_program_index_starts_at_one() -> None:
    with pytest.raises(ValueError, match=">= 1"):
        _run(program_id="prog-1", program_index=0)
    ok = _run(program_id="prog-1", program_index=1)
    assert ok.program_id == "prog-1"
    assert ok.program_index == 1


def test_standalone_run_is_unchanged() -> None:
    run = _run()
    assert run.program_id is None
    assert run.program_index is None


def test_transition_keeps_program_fields() -> None:
    run = _run(program_id="prog-1", program_index=2)
    moved = run.transition("START_COMPILE")
    assert moved.state != run.state
    assert moved.program_id == "prog-1"
    assert moved.program_index == 2


def test_with_manifest_and_protocol_source_keep_program_fields() -> None:
    from packages.domain.core import Digest
    from packages.domain.protocol_source import ProtocolSource

    run = _run(program_id="prog-1", program_index=3)
    refrozen = run.with_manifest(Digest.parse("sha256:" + "a" * 64))
    assert (refrozen.program_id, refrozen.program_index) == ("prog-1", 3)
    sourced = run.with_protocol_source(ProtocolSource(protocol_path="examples/protocols/x.yaml"))
    assert (sourced.program_id, sourced.program_index) == ("prog-1", 3)


def test_continue_rule_needs_at_least_one_verdict() -> None:
    with pytest.raises(ValueError, match="at least one verdict"):
        ProgramContinueRule(verdict_in=())
    with pytest.raises(ValueError, match="must not be empty"):
        ProgramContinueRule(verdict_in=("ACCEPT", ""))
    rule = ProgramContinueRule(verdict_in=("ACCEPT",))
    assert rule.verdict_in == ("ACCEPT",)


def test_program_requires_positive_guardrail_and_identities() -> None:
    rule = ProgramContinueRule(verdict_in=("ACCEPT",))
    with pytest.raises(ValueError, match="max_runs"):
        ResearchProgram(
            id="prog-1", project_id="p1", protocol_id="proto", max_runs=0, continue_rule=rule
        )
    with pytest.raises(ValueError, match="project_id"):
        ResearchProgram(
            id="prog-1", project_id="", protocol_id="proto", max_runs=1, continue_rule=rule
        )
    with pytest.raises(ValueError, match="protocol_id"):
        ResearchProgram(
            id="prog-1", project_id="p1", protocol_id="", max_runs=1, continue_rule=rule
        )
    with pytest.raises(ValueError, match="id"):
        ResearchProgram(id="", project_id="p1", protocol_id="proto", max_runs=1, continue_rule=rule)


def test_human_gate_is_optional_and_out_of_range_declarations_are_named() -> None:
    """GOAL-20261010-046 EC-02：闸门**可选**（缺省 = 不设），越界声明**点名**。

    三条臂：① 不声明 ⇒ `None`（既有行为逐字不变）；② 声明在位（含 `max_runs` **边界**
    上的取值）⇒ 逐字保留；③ 越界（太大 / 零 / 负数）⇒ `ValueError` 且**点名**声明值
    与上界 —— 「声明坏掉」不得被静默读成「没有闸门」（那会让声明了闸门的程序悄悄绕过人）。
    """
    rule = ProgramContinueRule(verdict_in=("ACCEPT",))

    def program(**overrides: object) -> ResearchProgram:
        base: dict[str, object] = {
            "id": "prog-1",
            "project_id": "p1",
            "protocol_id": "proto",
            "max_runs": 3,
            "continue_rule": rule,
        }
        base.update(overrides)
        return ResearchProgram(**base)  # type: ignore[arg-type]

    assert program().human_gate_at_index is None, "缺省必须是不设闸门"
    assert program(human_gate_at_index=2).human_gate_at_index == 2
    assert program(human_gate_at_index=3).human_gate_at_index == 3, "max_runs 本身是合法闸门位"
    for bad in (4, 0, -1):
        with pytest.raises(ValueError, match="human_gate_at_index must be within"):
            program(human_gate_at_index=bad)


def test_conditional_gate_is_optional_and_bad_declarations_are_named() -> None:
    """GOAL-20261010-048 EC-02：**条件式**闸门可选（缺省 = 不设），坏声明**点名**。

    四条臂：① 不声明 ⇒ `None`；② 声明在位 ⇒ 逐字保留；③ 三种坏声明（空集合 / 空串 /
    与序号声明**并存**）各自**点名** —— 「声明坏掉」不得被静默读成「没有闸门」；
    ④ 与序号声明**互斥**是**结构**上的（域层拒绝），不是推进时才发现的。
    """
    rule = ProgramContinueRule(verdict_in=("ACCEPT",))

    def program(**overrides: object) -> ResearchProgram:
        base: dict[str, object] = {
            "id": "prog-1",
            "project_id": "p1",
            "protocol_id": "proto",
            "max_runs": 3,
            "continue_rule": rule,
        }
        base.update(overrides)
        return ResearchProgram(**base)  # type: ignore[arg-type]

    assert program().human_gate_on_verdicts is None, "缺省必须是不设条件闸门"
    declared = program(human_gate_on_verdicts=("REJECT",))
    assert declared.human_gate_on_verdicts == ("REJECT",)
    assert declared.condition_gate_hit is True, "读面要能区分是哪条声明"

    with pytest.raises(ValueError, match="at least one verdict"):
        program(human_gate_on_verdicts=())
    with pytest.raises(ValueError, match="must not be empty strings"):
        program(human_gate_on_verdicts=("REJECT", ""))
    with pytest.raises(ValueError, match="mutually exclusive"):
        program(human_gate_at_index=1, human_gate_on_verdicts=("REJECT",))


def test_decision_kinds_separate_conclusion_from_guardrail() -> None:
    """结论面与护栏面**不共用种类**（否则「为何停」读不出是结论还是上界）。"""
    kinds = {kind.value for kind in ProgramDecisionKind}
    assert kinds == {
        "START",
        "CONTINUE",
        "STOP_RULE",
        "STOP_GUARDRAIL",
        "WAIT",
        "DEDUP",
        # GOAL-20261008-040 EC-02：失败面 / 取消面 / 重试面各归各的（互不混用）。
        "STOP_RUN_FAILED",
        "STOP_CANCELLED",
        "RETRY_FAILED_RUN",
        # GOAL-20261009-041 EC-02：**失败重试面的崩溃窗口**（认领了同序号却未落库）——
        # 与结论面的 `DEDUP` 同类不同面（那里认领的是**下一序号**的新 run）。
        # 同轮同步登记的**纯加法**：断言形态（集合相等）与判据口径一字未改。
        "DEDUP_FAILED_RUN",
        # GOAL-20261010-044 EC-02：**非终态面的两类等待必须可区分**（「等人」≠「等机器」）
        # —— `WAIT_FOR_APPROVAL` 与 `WAIT` 互不混用。同轮同步登记的**纯加法**：
        # 断言形态（集合相等）一字未改。
        "WAIT_FOR_APPROVAL",
    }


def test_decision_requires_reason_and_valid_index() -> None:
    with pytest.raises(ValueError, match="after_index"):
        ProgramDecision(
            program_id="prog-1", after_index=-1, kind=ProgramDecisionKind.START, reason="x"
        )
    with pytest.raises(ValueError, match="reason"):
        ProgramDecision(
            program_id="prog-1", after_index=0, kind=ProgramDecisionKind.START, reason=""
        )
    decision = ProgramDecision(
        program_id="prog-1",
        after_index=1,
        kind=ProgramDecisionKind.STOP_RULE,
        reason="verdict REVISE 不在规则里",
        cited_run_id="run-1",
        cited_facts=("verdict REVISE",),
    )
    assert decision.cited_facts == ("verdict REVISE",)
