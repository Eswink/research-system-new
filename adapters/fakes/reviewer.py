"""FakeReviewer：脚本化 judgment 与失败注入（timeout/malformed/unavailable）。"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from packages.application.evaluation.reviewer import ReviewAssignment
from packages.domain.eval_result import (
    ReviewerFinding,
    ReviewerVerdict,
)

FailureKind = str | None


@dataclass(frozen=True, slots=True)
class FakeReviewer:
    """按 reviewer_id 脚本化响应；无脚本时 FAIL。"""

    reviewer_id: str
    verdict: ReviewerVerdict = ReviewerVerdict.PASS
    rationale: str = "scripted"
    failure: FailureKind = None
    model_identity: str = "fake-model-v1"
    temperature: str = "0"

    def review(self, assignment: ReviewAssignment) -> ReviewerFinding:
        return ReviewerFinding(
            reviewer_id=self.reviewer_id,
            model_identity=self.model_identity,
            rubric_id=assignment.material.rubric.id,
            verdict=self.verdict,
            rationale=self.rationale,
            score=Decimal("1") if self.verdict is ReviewerVerdict.PASS else Decimal("0"),
            failure=self.failure,
            temperature=self.temperature,
            repetitions=1,
        )
