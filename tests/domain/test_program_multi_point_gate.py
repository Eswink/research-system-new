"""GOAL-20261011-055（`Z-1`）：**多点人工闸门**的声明面 —— 一组序号 + 越界 / 重复 / 混用点名。

**为什么单列**：`tests/domain/test_research_program.py` 已 205 行；本轮的靶子（多点声明）
自成一组，单列更清楚。

**判的是什么**：序 14 的单点形态类型是**单个**可选整数 ⇒ **结构上**只能声明一个点；
本条让它成为**一组**（`Z-1`：此前做不到「第 1 轮与第 3 轮各停一次等人拍板」）。
**缺省与单点形态逐字不变**；越界 / 重复 / 与另外两条声明混用一律**点名拒绝**。
"""

from __future__ import annotations

import pytest

from packages.domain.program import ProgramContinueRule, ResearchProgram


def _program(**overrides: object) -> ResearchProgram:
    base: dict[str, object] = {
        "id": "prog-1",
        "project_id": "p1",
        "protocol_id": "proto",
        "max_runs": 3,
        "continue_rule": ProgramContinueRule(verdict_in=("PASS",)),
    }
    base.update(overrides)
    return ResearchProgram(**base)  # type: ignore[arg-type]


def test_a_group_of_indexes_can_be_declared() -> None:
    """EC-02：**一组**序号可声明 —— 这是序 14 的单点形态**结构上做不到**的形态。"""
    declared = _program(human_gate_at_indexes=(1, 3))
    assert declared.human_gate_at_indexes == (1, 3)
    assert declared.multi_point_gate_hit is True, "读面要能区分是哪条声明"


def test_the_default_leaves_the_multi_point_gate_undeclared() -> None:
    """EC-02：**缺省 = 不设**（既有行为逐字不变）。"""
    assert _program().human_gate_at_indexes is None
    assert _program().multi_point_gate_hit is False


def test_a_single_point_declaration_is_still_usable_verbatim() -> None:
    """EC-02：**单点形态逐字保留**（序 14 的字段与语义都没动）。

    受判面**必须可区分**：本条与多点条的唯一差别是**用哪个字段** ——
    两条放在一起才证明新形态是**附加**而不是**替换**。
    """
    single = _program(human_gate_at_index=2)
    assert single.human_gate_at_index == 2
    assert single.human_gate_at_indexes is None, "单点声明不得顺带写多点字段"


def test_an_out_of_range_index_is_rejected_by_name() -> None:
    """EC-02：**越界**序号（超出 `1..max_runs`）⇒ **点名拒绝**（不静默截断）。"""
    with pytest.raises(ValueError, match=r"within 1\.\.max_runs"):
        _program(human_gate_at_indexes=(1, 9))
    # 受判面**可区分**：合法的那一组**不**报错（证明上一行判的是**越界**而非「有没有多点」）。
    assert _program(human_gate_at_indexes=(1, 3)).human_gate_at_indexes == (1, 3)


def test_a_repeated_index_is_rejected_by_name() -> None:
    """EC-02：**重复**序号 ⇒ **点名拒绝**（不静默去重 —— 静默会让声明看起来只写了一次）。"""
    with pytest.raises(ValueError, match="must not repeat"):
        _program(human_gate_at_indexes=(2, 2))


def test_an_empty_group_is_rejected_by_name() -> None:
    """EC-02：**空组** ⇒ 点名拒绝（`()` 与 `None` **语义不同**：声明了但没有点 vs 未声明）。"""
    with pytest.raises(ValueError, match="at least one index"):
        _program(human_gate_at_indexes=())


@pytest.mark.parametrize(
    "other",
    [
        {"human_gate_at_index": 1},
        {"human_gate_on_verdicts": ("REJECT",)},
    ],
)
def test_the_multi_point_form_is_mutually_exclusive_with_the_other_forms(
    other: dict[str, object],
) -> None:
    """EC-02：多点与**另外两条声明**互斥（混用 ⇒ 点名拒绝；既有互斥**不放宽**）。

    **参数化两条**：与单点混用、与条件式混用**都要**被拒 —— 只测一条会漏掉另一条路径。
    """
    overrides = {**other, "human_gate_at_indexes": (1, 3)}
    with pytest.raises(ValueError, match="mutually exclusive"):
        _program(**overrides)


def test_the_existing_exclusion_message_still_names_the_forms() -> None:
    """EC-02：互斥判词**点名涉及的形态**（「为什么停」要读得出是**哪两条**冲突了）。"""
    with pytest.raises(ValueError) as excinfo:
        _program(human_gate_at_index=1, human_gate_on_verdicts=("REJECT",))
    assert "human_gate_at_index" in str(excinfo.value)
    assert "human_gate_on_verdicts" in str(excinfo.value)
