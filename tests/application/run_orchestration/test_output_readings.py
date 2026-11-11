"""GOAL-20261111-109 EC-03：计划产物的**可数读数**与**两种「空」分开**。

**判什么**：

1. 三种读数各一条正例（design block 在 / 每臂参数 / 引用标识数——引用计数**有分母**）；
2. **两种「空」分得开**（GOAL-081 的教训）：`payload_absent`（读不到正文）≠
   `block_absent`（正文在、没写设计）——判据断言两者**点名不同**且各自可辨；
3. **反证**：参数越白名单 / 臂形态非法 ⇒ `arms_malformed` 点名，**不猜**、**不抛**；
4. **引用计数不靠正则猜**：不在已知分母里的 id 不算（混淆论证正批评这种形状）。
"""

from __future__ import annotations

from typing import Mapping, cast

from packages.application.run_orchestration.output_readings import (
    ArmReading,
    PlanOutputReadings,
    read_plan_payload,
)

KNOWN_IDS = ("mem-20261101-235", "mem-20261103-239")

_DESIGN = {
    "experiment_design": {
        "arms": {
            "control": {},
            "treatment": {"n_items": 120, "duplicate_pairs": 3},
        }
    }
}


def _payload(
    plan_text: str = "the plan cites mem-20261101-235 and builds on it",
    extra: Mapping[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {"content": plan_text}
    if extra:
        payload.update(extra)
    return payload


def test_all_three_readings_from_one_payload() -> None:
    """三种读数各一条正例（design block / 每臂参数 / 引用标识数）。"""
    readings = read_plan_payload(_payload(extra=_DESIGN), known_memory_ids=KNOWN_IDS)
    assert readings.source_state == "payload_present"
    assert readings.design_state == "block_present"
    assert readings.arms_state == "arms_parsed"
    assert readings.arm_count == 2
    assert readings.parameter_count == 2  # control 0 + treatment 2
    by_name = {arm.name: arm for arm in readings.arms}
    assert by_name["treatment"].parameters == (("duplicate_pairs", 3), ("n_items", 120))
    assert by_name["control"].parameters == ()
    assert readings.cited_memory_ids == ("mem-20261101-235",)


def test_both_arms_shape_forms_are_counted() -> None:
    """`parse_arms` 的两种形态（映射 / 显式列表）都出同样的可数读数。"""
    mapping_form = {"experiment_design": {"arms": {"control": {}, "treatment": {"n_items": 5}}}}
    list_form = {
        "experiment_design": {
            "arms": [
                {"name": "control", "parameters": {}},
                {"name": "treatment", "parameters": {"n_items": 5}},
            ],
        }
    }
    left = read_plan_payload(_payload(extra=mapping_form))
    right = read_plan_payload(_payload(extra=list_form))
    assert left.arms == right.arms
    assert left.arms_state == right.arms_state == "arms_parsed"


def test_two_kinds_of_empty_are_named_differently() -> None:
    """**两种「空」分得开**：读不到正文 ≠ 正文里没写设计（点名不同、互不顶替）。"""
    unreadable = read_plan_payload(None)
    assert unreadable.source_state == "payload_absent"
    assert unreadable.design_state == "block_absent"

    no_block = read_plan_payload(_payload("a plan with no design block"))
    assert no_block.source_state == "payload_present"
    assert no_block.design_state == "block_absent"

    # 三个点名字段合起来可辨：source_state 不同 ⇒ 两种空不会混同。
    assert unreadable.source_state != no_block.source_state


def test_non_mapping_payload_is_absent_not_crash() -> None:
    """载荷不是映射（例如空串 / 列表）⇒ `payload_absent`，**不抛**（读面不猜）。"""
    candidates: tuple[object, ...] = ("", [], 3)
    for bad in candidates:
        readings = read_plan_payload(cast("Mapping[str, object] | None", bad))
        assert readings.source_state == "payload_absent"


def test_arms_malformed_is_named_not_guessed() -> None:
    """**反证**：臂形态非法（列表项缺 name / 参数非映射）⇒ `arms_malformed` 点名。"""
    malformed = {"experiment_design": {"arms": ["not-a-mapping"]}}
    readings = read_plan_payload(_payload(extra=malformed))
    assert readings.arms_state == "arms_malformed"
    assert readings.arms == ()


def test_citation_counting_has_a_denominator() -> None:
    """**引用计数有分母**：不在 `known_memory_ids` 里的 id 形 token 不算（不猜）。"""
    text = "plan mentions mem-20261101-235 and also looks-like-mem-999999-999 randomly"
    readings = read_plan_payload(_payload(text), known_memory_ids=KNOWN_IDS)
    assert readings.cited_memory_ids == ("mem-20261101-235",)


def test_empty_denominator_yields_zero_citations() -> None:
    """分母为空（本 run 没有前序知识段）⇒ 引用数 0——这是**合法读数**不是缺口。"""
    readings = read_plan_payload(_payload("cites mem-20261101-235 anyway"), known_memory_ids=())
    assert readings.cited_memory_ids == ()


def test_readings_are_deterministic() -> None:
    """同一载荷读两遍 ⇒ 读数**逐字段相等**（消融比较的前提）。"""
    payload = _payload(extra=_DESIGN)
    left = read_plan_payload(payload, known_memory_ids=KNOWN_IDS)
    right = read_plan_payload(dict(payload), known_memory_ids=KNOWN_IDS)
    assert left == right


def test_arm_reading_is_countable() -> None:
    """`ArmReading` 的计数面（`parameter_count`）可用且非空真。"""
    arm = ArmReading(name="treatment", parameters=(("n_items", 120),))
    assert arm.parameter_count == 1
    readings = PlanOutputReadings(
        source_state="payload_present",
        design_state="block_present",
        arms_state="arms_parsed",
        arms=(arm,),
        cited_memory_ids=(),
    )
    assert readings.arm_count == 1 and readings.parameter_count == 1
