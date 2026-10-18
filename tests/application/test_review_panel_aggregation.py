"""GOAL-20261018-085 EC-02 / EC-03：**多评审聚合成一条建议性结论** + **独立性可判**。

**建档实测的缺口**：`evaluation/panel.py` 的 `run_panel` 在产品代码里**零构造点** ⇒
运行链上每件评审任务产出一条互不相干的判词，多评审**从不聚合**；于是「两个评审者给出
相反判词」在产品面上不产生任何可读事实。

**本文件判三组**：

- **EC-02 聚合**：多票 ⇒ 唯一最高票成 advisory；**平票 ⇒ `None` 并点名**；
  **全失败 ⇒ 无票且逐条点名**；**单评审 ⇒ `None`**（既有语义逐字不变）。
- **EC-03 独立性**：按**解析后的目标**判（与 GOAL-084 同源）；同目标两个实例 ⇒
  `independent=False` 并点名；异目标 ⇒ `True`；把第二个指回第一个的模型 ⇒ 翻转。
- **advisory 不夺真相权**：本模块**不**构造 `Decision`，也不改判词取值。
"""

from __future__ import annotations

from packages.application.evaluation.panel_verdict import (
    aggregate_panel,
    review_target,
)
from packages.domain.evidence import ReviewFinding


def _finding(
    finding_id: str,
    verdict: str,
    *,
    reviewer: str = "reviewer_a",
    model: str | None = "main/glm-5.3",
) -> ReviewFinding:
    return ReviewFinding(
        id=finding_id,
        review_type="acceptance_gate",
        verdict=verdict,
        findings=[f"{finding_id} wording"],
        reviewed_by=f"gate:{reviewer}",
        reviewer_model=model,
    )


# ------------------------------------------------------------ EC-02 聚合


def test_two_agreeing_votes_produce_that_advisory() -> None:
    panel = aggregate_panel([
        _finding("f-1", "PASS", reviewer="reviewer_a", model="main/glm-5.3"),
        _finding("f-2", "PASS", reviewer="reviewer_b", model="main/kimi-k2.6"),
    ])
    assert panel is not None
    assert panel.advisory == "PASS"
    assert panel.votes == {"PASS": 2}
    assert panel.dissent == ()


def test_opposing_votes_are_a_tie_and_name_no_advisory() -> None:
    """**平票 ⇒ `None`**（不猜），且少数意见**逐条点名**。"""
    panel = aggregate_panel([
        _finding("f-1", "PASS", reviewer="reviewer_a", model="main/glm-5.3"),
        _finding("f-2", "REJECT", reviewer="reviewer_b", model="main/kimi-k2.6"),
    ])
    assert panel is not None
    assert panel.advisory is None
    assert panel.decided is False
    assert panel.votes == {"PASS": 1, "REJECT": 1}


def test_majority_wins_and_the_minority_is_named() -> None:
    panel = aggregate_panel([
        _finding("f-1", "REJECT", reviewer="reviewer_a", model="main/glm-5.3"),
        _finding("f-2", "REJECT", reviewer="reviewer_b", model="main/kimi-k2.6"),
        _finding("f-3", "PASS", reviewer="reviewer_c", model="main/deepseek-v4-flash-vision"),
    ])
    assert panel is not None
    assert panel.advisory == "REJECT"
    # 少数意见的发言者取 `reviewed_by`（逐字 `gate:<agent id>`）—— 不伪造短名
    assert panel.dissent == ("gate:reviewer_c:PASS",)


def test_an_unattributed_finding_is_named_not_counted() -> None:
    """**设施面不折算**：没有模型身份的 finding **不进票数**，但**逐条点名**。"""
    panel = aggregate_panel([
        _finding("f-1", "PASS", reviewer="reviewer_a", model="main/glm-5.3"),
        _finding("f-2", "REJECT", reviewer="reviewer_b", model=None),
    ])
    assert panel is not None
    assert panel.voters == 1
    assert panel.votes == {"PASS": 1}
    assert panel.ineligible and "f-2" in panel.ineligible[0]
    assert panel.independent is False


def test_all_failures_leave_no_advisory_and_no_voters() -> None:
    panel = aggregate_panel([
        _finding("f-1", "PASS", reviewer="reviewer_a", model=None),
        _finding("f-2", "REJECT", reviewer="reviewer_b", model=None),
    ])
    assert panel is not None
    assert panel.advisory is None
    assert panel.voters == 0
    assert len(panel.ineligible) == 2


def test_a_single_review_is_not_aggregated() -> None:
    """**零回归边界**：单评审 ⇒ `None`（既有读面与判词逐字不变）。"""
    assert aggregate_panel([_finding("f-1", "PASS")]) is None
    assert aggregate_panel([]) is None


def test_aggregation_is_deterministic() -> None:
    findings = [
        _finding("f-1", "PASS", reviewer="reviewer_b", model="main/glm-5.3"),
        _finding("f-2", "REJECT", reviewer="reviewer_a", model="main/kimi-k2.6"),
    ]
    runs = {repr(aggregate_panel(findings).as_payload()) for _ in range(20)}  # type: ignore[union-attr]
    assert len(runs) == 1


# --------------------------------------------------------- EC-03 独立性


def test_distinct_targets_are_independent() -> None:
    panel = aggregate_panel([
        _finding("f-1", "PASS", reviewer="reviewer_a", model="main/glm-5.3"),
        _finding("f-2", "PASS", reviewer="reviewer_b", model="main/kimi-k2.6"),
    ])
    assert panel is not None
    assert panel.independent is True
    assert panel.independence_notes == ()
    assert panel.targets == ("main/glm-5.3", "main/kimi-k2.6")


def test_the_same_target_twice_is_not_an_independent_panel() -> None:
    """**核心反证**：两个 reviewer id 不同、但**目标是同一个** ⇒ 不是独立复核，并点名。"""
    panel = aggregate_panel([
        _finding("f-1", "PASS", reviewer="reviewer_a", model="main/deepseek-v4-flash-vision"),
        _finding("f-2", "PASS", reviewer="reviewer_b", model="main/deepseek-v4-flash-vision"),
    ])
    assert panel is not None
    assert panel.independent is False
    assert any("share the same target" in note for note in panel.independence_notes)
    assert panel.targets == ("main/deepseek-v4-flash-vision",)


def test_pointing_the_second_reviewer_back_flips_the_conclusion() -> None:
    """**成对**：只改第二个评审者的目标 ⇒ `independent` 翻转。"""
    distinct = aggregate_panel([
        _finding("f-1", "PASS", reviewer="reviewer_a", model="main/glm-5.3"),
        _finding("f-2", "PASS", reviewer="reviewer_b", model="main/kimi-k2.6"),
    ])
    same = aggregate_panel([
        _finding("f-1", "PASS", reviewer="reviewer_a", model="main/glm-5.3"),
        _finding("f-2", "PASS", reviewer="reviewer_b", model="main/glm-5.3"),
    ])
    assert distinct is not None and same is not None
    assert distinct.independent is True
    assert same.independent is False


def test_the_same_model_name_on_different_endpoints_is_independent() -> None:
    """目标 = `(endpoint, model_name)`：同名不同 endpoint **不算**同一个（与 GOAL-084 同源）。"""
    panel = aggregate_panel([
        _finding("f-1", "PASS", reviewer="reviewer_a", model="main/deepseek-v4-flash-vision"),
        _finding("f-2", "PASS", reviewer="reviewer_b", model="other/deepseek-v4-flash-vision"),
    ])
    assert panel is not None
    assert panel.independent is True


def test_review_target_refuses_half_a_target() -> None:
    assert review_target(endpoint_id="main", model_name="glm-5.3") == "main/glm-5.3"
    assert review_target(endpoint_id=None, model_name="glm-5.3") is None
    assert review_target(endpoint_id="main", model_name=None) is None


# ------------------------------------------------- advisory 不夺真相权


def test_the_aggregate_does_not_produce_a_decision() -> None:
    """**射程边界**：聚合只产出 `PanelVerdict`，**不**构造 `Decision`（真相权仍在验收门）。"""
    from packages.application.evaluation import panel_verdict as module

    source = module.__file__ or ""
    from pathlib import Path

    text = Path(source).read_text(encoding="utf-8")
    assert "Decision(" not in text, "聚合面不得构造 Decision"
    assert "decided_by" not in text, "聚合面不得写 Decision 的作者面"
