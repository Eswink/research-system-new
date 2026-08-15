"""M11 Reviewer Panel 测试：独立聚合、disagreement、partial/total failure。"""

from __future__ import annotations

import pytest

from adapters.fakes.reviewer import FakeReviewer
from packages.application.evaluation.panel import (
    PanelStatus,
    run_panel,
)
from packages.application.evaluation.reviewer import (
    ReviewAssignment,
    ReviewMaterial,
)
from packages.domain.eval_result import ReviewerVerdict
from packages.domain.eval_spec import RubricSpec


def _assignment() -> ReviewAssignment:
    return ReviewAssignment(
        reviewer_id="panel",
        material=ReviewMaterial(
            case_id="c1",
            rubric=RubricSpec("r1", "soundness", "is it sound"),
            material_ref="artifact://c1/main",
            system_version="0.4.0",
        ),
    )


def test_panel_complete_agreement() -> None:
    reviewers = (
        FakeReviewer(reviewer_id="rev-a", verdict=ReviewerVerdict.PASS),
        FakeReviewer(reviewer_id="rev-b", verdict=ReviewerVerdict.PASS),
        FakeReviewer(reviewer_id="rev-c", verdict=ReviewerVerdict.PASS),
    )
    result = run_panel(_assignment(), reviewers)
    assert result.status is PanelStatus.COMPLETE
    assert result.aggregation is ReviewerVerdict.PASS
    assert result.votes == {"PASS": 3}
    assert result.disagreement == ()
    assert result.independent


def test_panel_disagreement_is_recorded_not_collapsed() -> None:
    reviewers = (
        FakeReviewer(reviewer_id="rev-a", verdict=ReviewerVerdict.PASS),
        FakeReviewer(reviewer_id="rev-b", verdict=ReviewerVerdict.FAIL),
    )
    result = run_panel(_assignment(), reviewers)
    assert result.status is PanelStatus.COMPLETE
    assert result.aggregation is None  # 平票：无多数结论
    assert result.votes == {"PASS": 1, "FAIL": 1}
    assert result.disagreement == ("rev-a:PASS", "rev-b:FAIL")


def test_panel_partial_failure_is_structured() -> None:
    reviewers = (
        FakeReviewer(reviewer_id="rev-a", verdict=ReviewerVerdict.PASS),
        FakeReviewer(
            reviewer_id="rev-b",
            verdict=ReviewerVerdict.AMBIGUOUS,
            failure="timeout",
        ),
    )
    result = run_panel(_assignment(), reviewers)
    assert result.status is PanelStatus.PARTIAL_FAILURE
    assert result.votes == {"PASS": 1}
    assert result.aggregation is ReviewerVerdict.PASS
    assert result.independent


def test_panel_total_failure_is_not_a_judgment() -> None:
    reviewers = (
        FakeReviewer(
            reviewer_id="rev-a",
            verdict=ReviewerVerdict.AMBIGUOUS,
            failure="timeout",
        ),
        FakeReviewer(
            reviewer_id="rev-b",
            verdict=ReviewerVerdict.AMBIGUOUS,
            failure="unavailable",
        ),
    )
    result = run_panel(_assignment(), reviewers)
    assert result.status is PanelStatus.TOTAL_FAILURE
    assert result.votes == {}
    assert result.aggregation is None


def test_panel_requires_two_reviewers() -> None:
    with pytest.raises(ValueError, match="at least 2"):
        run_panel(
            _assignment(),
            (FakeReviewer(reviewer_id="rev-a"),),
        )


def test_panel_does_not_copy_same_reviewer_as_independent() -> None:
    # 相同 identity 的重复判断不被当作独立 panel（由调用方保证 distinct）
    reviewers = (
        FakeReviewer(reviewer_id="rev-a", verdict=ReviewerVerdict.PASS),
        FakeReviewer(reviewer_id="rev-a", verdict=ReviewerVerdict.FAIL),
    )
    result = run_panel(_assignment(), reviewers)
    assert result.independent is False
