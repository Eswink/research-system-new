"""GOAL-20261111-109 EC-02：`AblationPair` 的**「只差一个 slot」机械证明**。

**夹具形状 = 产品形状**：`AgentSessionSpec` 的各 prompt 字段携带**已渲染的 `str | None`**
（`session_prompts.*_prompt` 的返回）——消融作用在**会话真正收到的那份提示词**上。
第一版夹具塞了视图 dict，被产品渲染器静默丢段（`_section_of` 只认 str / 视图对象），
两臂假相等 —— 判据当场抓到。

四条（EC-02 判据 ① + 反证 ②，外加边界按压）：

1. **正例（判据 ①）**：两臂 manifest 的 `comparison_digest` **相等**（同一份装配）+
   `only_slot_differs()` 为真 + `differing_sections()` **恰是** `{slot}`；
2. **反证（判据 ②）**：把被消融段换一个字 ⇒ 两臂渲染必然不同（内容真被比）；
   把**别的**段换一个字 ⇒ `only_slot_differs()` 判**假**（它真在逐段比）；
3. **边界**：未知段名 / present 缺席 / absent 在场 / 非字符串段值 / 两臂 manifest
   漂移——每种**点名拒绝**（构造期，fail-closed）；
4. **词表**：slot 名就是产品 `compose_prompt` 的六个形参；absent 臂在被消融段缺席时
   恰等于纯 purpose + 其余段（不凭空多出被消融段的影子）。
"""

from __future__ import annotations

import dataclasses

import pytest

from packages.application.run_orchestration.ablation import (
    SLOT_ORDER,
    AblationPair,
    PromptArm,
    build_pair,
)
from packages.application.run_orchestration.comparison_digest import comparison_digest
from packages.domain.core import Version
from packages.domain.manifest import RunManifest

#: 各段的**已渲染**文本（产品把 str 直接交给 `compose_prompt`，`_section_of` 原样用）。
DIRECTION = "DIR: retrieval augmentation for scientific hypothesis generation"
PRIOR = "PRIOR: RAG improves factual grounding (source: memory)"
RETRIEVAL = "- [1] 39284801: Retrieval helps hypotheses\n- [2] 42787049: A second study"
REVIEW_OUTCOME = "PRIOR REVIEW: verdict=REVISE"
REVIEW_POINTS = "REVIEW POINTS: P1 strengthen the baseline"
REVIEW_MATERIAL = "UNDER REVIEW: (the draft body)"

_SLOTS: dict[str, str | None] = {
    "direction": DIRECTION,
    "prior_knowledge": PRIOR,
    "retrieval": RETRIEVAL,
    "review_outcome": REVIEW_OUTCOME,
    "review_points": REVIEW_POINTS,
    "review_material": REVIEW_MATERIAL,
}


def _manifest() -> RunManifest:
    return RunManifest(
        run_id="run-a",
        project_id="proj-1",
        protocol_version=Version(text="1.0.0"),
        resolved_models={"writer": "hy4free"},
    )


def _arm(**slot_overrides: str | None) -> PromptArm:
    return PromptArm(manifest=_manifest(), slots={**_SLOTS, **slot_overrides})


def test_two_arms_share_the_assembly_and_differ_in_exactly_one_slot() -> None:
    """**正例（判据 ①）**：同装配 + 只差一个 slot，差异面恰是那个 slot。"""
    pair = build_pair(_manifest(), _SLOTS, "retrieval")
    assert comparison_digest(pair.present.manifest).digest == (
        comparison_digest(pair.absent.manifest).digest
    ), "两臂必须共享同一份装配"
    assert pair.only_slot_differs()
    assert pair.differing_sections() == ("retrieval",)
    present_text, absent_text = pair.renders("PURPOSE")
    assert present_text != absent_text
    # 被消融段的贡献文本只在一臂里（byte 级，不是子串判据的「出现过」）。
    assert RETRIEVAL in present_text and RETRIEVAL not in absent_text


def test_each_slot_can_be_the_ablated_one() -> None:
    """词表六个段**逐个**都能当被消融段（机制不挑段；试点只面向「计划」域）。"""
    for slot in SLOT_ORDER:
        pair = build_pair(_manifest(), _SLOTS, slot)
        assert pair.only_slot_differs(), slot
        assert pair.differing_sections() == (slot,), slot


def test_drifting_another_slot_breaks_the_proof() -> None:
    """**反证（判据 ② 的另一半）**：把**别的**段换一个字 ⇒ 证明判**假**。

    若 `only_slot_differs` 只看被消融段，这里不会红——而两臂就不再是
    「只差一个变量」，消融结论作废。**本判据咬的就是这个**。
    """
    drifted: dict[str, str | None] = {**_SLOTS, "direction": DIRECTION + "X", "retrieval": None}
    pair = AblationPair(
        slot="retrieval",
        present=_arm(),
        absent=PromptArm(manifest=_manifest(), slots=drifted),
    )
    assert not pair.only_slot_differs()
    assert set(pair.differing_sections()) == {"retrieval", "direction"}


def test_drifting_the_ablated_slot_is_still_a_valid_pair() -> None:
    """**反证（判据 ②）**：被消融段换一个字 ⇒ 两臂渲染必然不同（内容真被比）。"""
    pair = AblationPair(
        slot="retrieval",
        present=_arm(retrieval=RETRIEVAL + " (updated)"),
        absent=_arm(retrieval=None),
    )
    present_text, absent_text = pair.renders("PURPOSE")
    assert present_text != absent_text
    assert pair.only_slot_differs()
    assert pair.differing_sections() == ("retrieval",)


def test_the_renders_come_from_the_product_composer() -> None:
    """两臂渲染走**产品唯一拼装点**：只消融 direction 时 absent 臂恰等于纯 purpose。"""
    only_retrieval: dict[str, str | None] = {name: None for name in SLOT_ORDER}
    only_retrieval["retrieval"] = RETRIEVAL
    pair = build_pair(_manifest(), only_retrieval, "retrieval")
    present_text, absent_text = pair.renders("PURPOSE")
    assert absent_text == "PURPOSE"
    assert present_text == f"PURPOSE\n\n{RETRIEVAL}"
    # 顺序 = compose_prompt 的固定拼装序（direction 最先、被评对象最后）。
    full = build_pair(_manifest(), _SLOTS, "review_material").renders("PURPOSE")[0]
    assert full.index(DIRECTION) < full.index(PRIOR) < full.index(RETRIEVAL)
    assert full.index(REVIEW_OUTCOME) < full.index(REVIEW_POINTS) < full.index(REVIEW_MATERIAL)


def test_an_empty_slot_contributes_nothing() -> None:
    """空串段与缺席段的 digest **不同**（`""` 是在场但空，`None` 是缺席——分得开）。"""
    arm_empty = _arm(review_material="")
    arm_absent = _arm(review_material=None)
    assert (
        arm_empty.section_digests()["review_material"]
        != (arm_absent.section_digests()["review_material"])
    )
    pair = AblationPair(slot="review_material", present=arm_empty, absent=arm_absent)
    assert pair.only_slot_differs()


def test_arms_whose_manifests_drift_are_refused() -> None:
    """两臂 manifest 声明字段漂移 ⇒ 不再是「同一份装配」⇒ 构造期点名拒绝。"""
    other = dataclasses.replace(_manifest(), resolved_models={"writer": "hy3"})
    with pytest.raises(ValueError, match="not the same assembly"):
        AblationPair(
            slot="retrieval",
            present=_arm(),
            absent=PromptArm(manifest=other, slots={name: None for name in SLOT_ORDER}),
        )


def test_degenerate_pairs_are_refused_by_name() -> None:
    """未知段名 / present 缺席 / absent 在场 / 非字符串段值——各**点名**拒绝。"""
    with pytest.raises(ValueError, match="unknown ablation slot"):
        build_pair(_manifest(), _SLOTS, "nope")
    with pytest.raises(ValueError, match="already absent"):
        build_pair(_manifest(), {**_SLOTS, "review_material": None}, "review_material")
    with pytest.raises(ValueError, match="present arm must carry"):
        AblationPair(
            slot="retrieval",
            present=_arm(retrieval=None),
            absent=_arm(retrieval=None),
        )
    with pytest.raises(ValueError, match="absent arm must not carry"):
        AblationPair(slot="retrieval", present=_arm(), absent=_arm())
    with pytest.raises(ValueError, match="unknown prompt slots"):
        PromptArm(manifest=_manifest(), slots={"directions": "x"})
    with pytest.raises(ValueError, match="must be a rendered str"):
        PromptArm(manifest=_manifest(), slots={**_SLOTS, "retrieval": {"entries": []}})  # type: ignore[dict-item]
