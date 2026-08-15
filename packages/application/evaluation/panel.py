"""M11 Reviewer Panel：独立 judgments 聚合、disagreement 与 partial failure。

约束：
- 每个 reviewer 独立判断同一 ReviewMaterial（judgment 互不共享）；
- disagreement 被显式记录为 disagreement 而非折叠成多数；
- partial panel failure（部分 reviewer 设施故障）→ 结构化 PanelResult
  状态 INFRA_DEGRADED，绝不冒充独立 panel 的完整结论；
- 简单多数聚合只产出 advisory aggregation（reviewer 不是 truth owner）。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from packages.application.evaluation.reviewer import (
    ReviewAssignment,
    Reviewer,
)
from packages.domain.eval_result import (
    ReviewerFinding,
    ReviewerVerdict,
)


class PanelStatus(StrEnum):
    """panel 执行状态；PARTIAL_FAILURE 表示部分 reviewer 设施故障。"""

    COMPLETE = "COMPLETE"
    PARTIAL_FAILURE = "PARTIAL_FAILURE"
    TOTAL_FAILURE = "TOTAL_FAILURE"


@dataclass(frozen=True, slots=True)
class PanelResult:
    """panel 输出：全部 finding + 结构化聚合与分歧记录。"""

    rubric_id: str
    findings: tuple[ReviewerFinding, ...]
    status: PanelStatus
    votes: dict[str, int]
    disagreement: tuple[str, ...]
    aggregation: ReviewerVerdict | None = None

    @property
    def independent(self) -> bool:
        """judgments 必须来自不同 reviewer identity。"""

        identities = {item.reviewer_id for item in self.findings}
        return len(identities) == len(self.findings)


def run_panel(
    assignment: ReviewAssignment,
    reviewers: tuple[Reviewer, ...],
) -> PanelResult:
    """对同一 material 运行独立 reviewer 集合并聚合。

    reviewer 数量少于 2 视为配置错误（panel 语义不成立），
    抛 ValueError（由 runner 转为 INFRA）。
    """

    if len(reviewers) < 2:
        raise ValueError("panel requires at least 2 reviewers")
    findings = tuple(reviewer.review(assignment) for reviewer in reviewers)
    rubric_id = assignment.material.rubric.id
    failed = [item for item in findings if item.failure is not None]
    votes = _count_verdicts(findings)
    disagreements = _disagreements(findings)
    if len(failed) == len(findings):
        status = PanelStatus.TOTAL_FAILURE
    elif failed:
        status = PanelStatus.PARTIAL_FAILURE
    else:
        status = PanelStatus.COMPLETE
    aggregation = _majority_verdict(votes)
    return PanelResult(
        rubric_id=rubric_id,
        findings=findings,
        status=status,
        votes=votes,
        disagreement=disagreements,
        aggregation=aggregation,
    )


def _count_verdicts(findings: tuple[ReviewerFinding, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in findings:
        if item.failure is None:
            key = item.verdict.value
            counts[key] = counts.get(key, 0) + 1
    return counts


def _disagreements(findings: tuple[ReviewerFinding, ...]) -> tuple[str, ...]:
    verdicts = {item.verdict.value for item in findings if item.failure is None}
    if len(verdicts) <= 1:
        return ()
    return tuple(f"{item.reviewer_id}:{item.verdict.value}" for item in findings)


def _majority_verdict(votes: dict[str, int]) -> ReviewerVerdict | None:
    if not votes:
        return None
    ranked = sorted(votes.items(), key=lambda item: (-item[1], item[0]))
    top_count = ranked[0][1]
    if sum(1 for _, count in ranked if count == top_count) > 1:
        return None
    return ReviewerVerdict(ranked[0][0])
