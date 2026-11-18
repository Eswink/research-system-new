"""GOAL-20261117-114 EC-04：**读数 → 观测**的唯一映射（配对消融缺的那一步）。

**它补哪一道缝**（本轮勘测实测）：GOAL-109 交付了两半 —— `output_readings.read_plan_payload`
（计划制品 → 可数读数，三态字符串）与 `tools/ablation_report.py`（四列位移 +
`MIN_CORPUS=3` 门，要求四个 **`int`**）。**中间那一步没有任何代码**：抓一次真实 run
之后，没有任何东西能把它的产物变成一份可喂给门的观测 ⇒ 「读数的采集器」（GOAL-109
`W-2`）四轮没人接。

**判什么**（每条都指向一个会假绿的具体形态）：

1. **四列都是 `int`、且不是 `bool`**：`ablation_report._observation` 显式拒 `bool`；
   而 `design_state == "block_present"` 天然产 bool ⇒ 直接塞进去会在**真实 run 上**被门
   拒绝，而单测夹具（`design_block: 1`）永远不暴露这个形态；
2. **三态映射逐格钉死**：`block_present`/`arms_absent` 是「设计写了、臂没写」（1/0/0），
   `block_absent` 是「产出里没设计」（0/0/0）—— 两种「空」不得互相顶替；
3. **闭环**：映射结果直接喂 `tools/ablation_report.build_report` ⇒ 门接受、四列渲染、
   措辞守卫不抛（否则「映射对了」与「工具能吃」是两件没接上的事）；
4. **反证（闭集外点名拒绝）**：伪造 `source_state` ⇒ 抛错并点名，**不**回落成 0；
5. **反证（缺可比键）**：空 `comparison_digest` ⇒ 抛错（没有键的观测在门那里必被拒，
   这里提前点名而不是让它在 3 个 run 之后才暴露）。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

from packages.application.run_orchestration.ablation_observations import (
    READING_KEYS,
    AblationObservationError,
    observation_from,
)
from packages.application.run_orchestration.output_readings import (
    PlanOutputReadings,
    read_plan_payload,
)

ROOT = Path(__file__).resolve().parents[3]
REPORT_TOOL = ROOT / "tools" / "ablation_report.py"

#: 一份真实形状的计划载荷（`research_report_plan` 合约要的形态；两条臂 + 一个引用）。
_PLAN = (
    "This study asks whether duplicate detection cost grows with corpus size.\n"
    "It builds on mem-20261114-113 (the stored PROJECT memory).\n"
    "```experiment_design\n"
    '{"experiment_design": {"arms": {"treatment": {"seed": 17, "n_items": 120},'
    ' "control": {"seed": 17}}}}\n'
    "```\n"
)
_KNOWN = ("mem-20261114-113",)


def _load_report() -> ModuleType:
    module = sys.modules.get("goal114_ablation_report")
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location("goal114_ablation_report", REPORT_TOOL)
    assert spec is not None and spec.loader is not None, REPORT_TOOL
    loaded = importlib.util.module_from_spec(spec)
    sys.modules["goal114_ablation_report"] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def _readings(payload: object, *, known: tuple[str, ...] = _KNOWN) -> PlanOutputReadings:
    return read_plan_payload(payload if isinstance(payload, dict) else None, known_memory_ids=known)


def test_the_four_columns_are_ints_and_never_booleans() -> None:
    """四列必须是 `int` 且 `type(...) is int`（`bool` 是 `int` 的子类，会骗过 isinstance）。"""
    observation = observation_from(_readings({"content": _PLAN}), comparison_digest="sha256:aa")
    for key in READING_KEYS:
        assert type(observation[key]) is int, f"{key} 不是 int（bool 会被消融门拒）"


def test_a_full_plan_maps_to_the_four_readings() -> None:
    """正例：两条臂 + 三个参数 + 一个引用。"""
    observation = observation_from(_readings({"content": _PLAN}), comparison_digest="sha256:aa")
    assert observation["design_block"] == 1
    assert observation["arm_count"] == 2
    assert observation["parameter_count"] == 3
    assert observation["citation_count"] == 1


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        # 设计写了、臂没写：`design_block=1` 但臂数为 0（是**事实**，不是「没读到」）。
        ({"content": "a plan with a design block but no arms\n"}, (0, 0, 0)),
        # 正文在、设计块缺席：四列全 0（「产出里没写设计」）。
        ({"content": "a plan with no design block at all\n"}, (0, 0, 0)),
        # 完全没有载荷：四列全 0（「没有产出」）。
        (None, (0, 0, 0)),
    ],
)
def test_the_three_empty_states_each_map_without_guessing(
    payload: object, expected: tuple[int, int, int]
) -> None:
    """两种「空」与「没产出」各自映射；`block_absent` 不得因为「有正文」就记 1。"""
    observation = observation_from(_readings(payload), comparison_digest="sha256:aa")
    assert (
        observation["arm_count"],
        observation["parameter_count"],
        observation["citation_count"],
    ) == expected


def test_the_block_present_state_is_one_and_the_others_are_zero() -> None:
    """`block_present` ⇒ 1；`block_absent` ⇒ 0（逐格钉，不靠上面那条的三元组）。"""
    present = observation_from(_readings({"content": _PLAN}), comparison_digest="sha256:aa")
    absent = observation_from(
        _readings({"content": "no block here"}), comparison_digest="sha256:aa"
    )
    assert present["design_block"] == 1
    assert absent["design_block"] == 0


def test_an_observation_is_accepted_by_the_ablation_gate() -> None:
    """**闭环**：观测直接喂 `build_report` ⇒ 门接受、四列在场、措辞守卫不抛。"""
    report_tool = _load_report()
    observation = observation_from(_readings({"content": _PLAN}), comparison_digest="sha256:aa")
    raw = {
        "slot": "prior_knowledge",
        "pairs": [
            {"label": f"k{index}", "present": observation, "absent": observation}
            for index in range(1, report_tool.MIN_CORPUS + 1)
        ],
    }
    report = report_tool.build_report(raw)
    assert report.gate.sufficient is True
    assert [column.field for column in report.shifts] == list(READING_KEYS)
    text = report_tool.render_report(report)
    assert "prior_knowledge" in text


def test_a_state_outside_the_closed_set_is_refused_by_name() -> None:
    """反证：闭集外的 `source_state` ⇒ 抛错并点名（**不**回落成 0）。"""
    bogus = PlanOutputReadings(
        source_state="something_else",
        design_state="block_absent",
        arms_state="arms_absent",
        arms=(),
        cited_memory_ids=(),
    )
    with pytest.raises(AblationObservationError) as caught:
        observation_from(bogus, comparison_digest="sha256:aa")
    assert "something_else" in str(caught.value)


def test_a_missing_comparison_digest_is_refused_by_name() -> None:
    """反证：空可比键 ⇒ 抛错（让它在观测点暴露，而不是在 3 个 run 之后）。"""
    with pytest.raises(AblationObservationError) as caught:
        observation_from(_readings({"content": _PLAN}), comparison_digest="")
    assert "comparison_digest" in str(caught.value)
