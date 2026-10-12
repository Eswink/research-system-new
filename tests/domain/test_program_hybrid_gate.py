"""GOAL-20261012-060（序 28）：**闸门声明的混合式** —— EC-02 / EC-03 的判据。

**为什么单列**：本轮的靶子（**两维同时生效**的声明 + 两维**各自点名**）自成一组；
与 `test_program_multi_point_gate.py`（序 23 的多点）/ `test_research_program.py`
（序 14/16 的单点与条件式）**分工不同** —— 那两组判各自那一维，本组判**组合**。

**判的是什么**：三条既有声明**互斥**（`_validate_gate_exclusivity`）⇒ 「第 1、3 轮停，
**且**判词为 X 时也停」**结构上做不到**。本轮加**混合式**（序号组 × 取值集合）：
**任一维命中即停**，判词**点名命中的维**（两维都命中 ⇒ **两条都点名**）。
"""

from __future__ import annotations

import pytest

from packages.domain.program import (
    HybridGateDeclaration,
    ProgramContinueRule,
    ResearchProgram,
)


def _program(**overrides: object) -> ResearchProgram:
    base: dict[str, object] = {
        "id": "prog-hybrid",
        "project_id": "p1",
        "protocol_id": "proto",
        "max_runs": 3,
        "continue_rule": ProgramContinueRule(verdict_in=("ACCEPT",)),
    }
    base.update(overrides)
    return ResearchProgram(**base)  # type: ignore[arg-type]


def test_the_hybrid_form_can_be_declared() -> None:
    """EC-02：混合式**可声明**（此前「两条同时声明」结构上被互斥拒绝）。"""
    program = _program(
        human_gate_hybrid=HybridGateDeclaration(at_indexes=(1, 3), on_verdicts=("REJECT",))
    )
    assert program.hybrid_gate_hit is True
    assert program.human_gate_hybrid is not None
    assert program.human_gate_hybrid.at_indexes == (1, 3)


def test_the_other_three_declarations_are_untouched() -> None:
    """EC-02：三条既有声明**逐字仍在**（本轮只**加**一种形态）。"""
    assert _program(human_gate_at_index=2).condition_gate_hit is False
    assert _program(human_gate_at_index=2).multi_point_gate_hit is False
    assert _program(human_gate_at_index=2).hybrid_gate_hit is False
    assert _program(human_gate_on_verdicts=("X",)).condition_gate_hit is True
    assert _program(human_gate_at_indexes=(1,)).multi_point_gate_hit is True


def test_the_undeclared_form_stays_none_verbatim() -> None:
    """EC-02：**未声明** ⇒ 三种读面都是 `False`（既有行为逐字不变）。"""
    program = _program()
    assert program.hybrid_gate_hit is False
    assert program.human_gate_hybrid is None


def test_a_half_declaration_cannot_be_constructed() -> None:
    """EC-02：**只声明一半**在构造上写不出来（值对象 ``__post_init__`` 拒绝）。

    受判面 = **两个维度各自**（空序号组 / 空取值集合）—— 少一半就不是混合式。
    """
    with pytest.raises(ValueError, match="at_indexes must name at least one index"):
        HybridGateDeclaration(at_indexes=(), on_verdicts=("X",))
    with pytest.raises(ValueError, match="on_verdicts must name at least one verdict"):
        HybridGateDeclaration(at_indexes=(1,), on_verdicts=())


def test_an_empty_verdict_string_is_refused() -> None:
    """EC-02：空判词**点名拒绝**（与序 16 的条件式**同一纪律**）。"""
    with pytest.raises(ValueError, match="must not be empty strings"):
        HybridGateDeclaration(at_indexes=(1,), on_verdicts=("",))


def test_an_out_of_range_index_is_refused_by_name() -> None:
    """EC-02：越界点**点名拒绝**（那一轮永远不会触发 —— 与序 23 多点**同一理由**）。"""
    with pytest.raises(ValueError, match="within 1..max_runs"):
        _program(human_gate_hybrid=HybridGateDeclaration(at_indexes=(1, 9), on_verdicts=("X",)))


def test_a_repeated_index_is_refused_by_name() -> None:
    """EC-02：重复点**点名拒绝**（会让「这一轮为什么停」看起来像声明了两次）。

    重复检查在 `ResearchProgram` 那一层（它要看 `max_runs` ⇒ 与越界检查同处一层；
    值对象看不见 `max_runs`，所以只保证非空）。
    """
    with pytest.raises(ValueError, match="must not repeat an index"):
        _program(human_gate_hybrid=HybridGateDeclaration(at_indexes=(1, 1), on_verdicts=("X",)))


def test_the_hybrid_form_stays_exclusive_with_the_other_declarations() -> None:
    """EC-02：混合式与**其余三条**仍**互斥**（同时声明 ⇒ 点名拒绝）。

    受判面 = **三条各自**（不是「随便挑一条」）—— 少测一条会漏掉一整类并存。
    """
    hybrid = HybridGateDeclaration(at_indexes=(1,), on_verdicts=("X",))
    for extra in (
        {"human_gate_at_index": 1},
        {"human_gate_on_verdicts": ("Y",)},
        {"human_gate_at_indexes": (2,)},
    ):
        with pytest.raises(ValueError, match="mutually exclusive"):
            _program(human_gate_hybrid=hybrid, **extra)


def test_the_existing_exclusivity_between_the_three_is_untouched() -> None:
    """EC-02 反证臂：**既有三条之间**的互斥**未被放宽**（本轮不解除那条纪律）。"""
    with pytest.raises(ValueError, match="mutually exclusive"):
        _program(human_gate_at_index=1, human_gate_on_verdicts=("X",))


def test_the_nudge_bound_stays_orthogonal_to_the_hybrid_form() -> None:
    """EC-02：序 24 的时限面与混合式**正交**（可同时声明 —— 不参与互斥）。"""
    program = _program(
        human_gate_hybrid=HybridGateDeclaration(at_indexes=(1,), on_verdicts=("X",)),
        gate_nudge_after_seconds=60,
    )
    assert program.gate_nudge_after_seconds == 60
    assert program.hybrid_gate_hit is True
