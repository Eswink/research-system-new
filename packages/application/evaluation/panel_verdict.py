"""评审小组的**聚合面**（GOAL-20261018-085 EC-02 / EC-03）。

**它补哪一格**：`evaluation/panel.py` 的 `run_panel` 早已存在（多数票 + 分歧 + 部分失败
三态），但它在**产品代码里零构造点** —— 运行链上每件评审任务产出一条互不相干的
`ReviewFinding`，多评审**从不聚合**。于是「两个评审者给出相反判词」这件事在产品面上
不产生任何**可读**的事实。

**本模块的三条边界**（逐条可判）：

1. **advisory，不夺真相权**：聚合结论是 `advisory`。`Decision` 仍由验收门
   （`evaluation_gate.evaluate_task_gate`）给出；本模块**不**构造、不改写 `Decision`。
2. **设施失败不折算**：一条 finding 的 `verdict` 说明不了什么时（未参与 / 无法解析），
   它**不进票数**，但**必须逐条点名** —— 把失败折算成「判负」或「判过」都是伪造。
3. **独立性与 GOAL-084 同源**：按**解析后的执行目标**（`(endpoint, model_name)`）判，
   不认 agent id / reviewer id。同目标两个实例 ⇒ **不是独立复核**（哪怕 id 不同）。

**确定性**：同输入同输出（票数按固定键序求和、结论按固定优先级取），零出网零模型零时钟。
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from packages.domain.evidence import ReviewFinding

#: 评审目标的稳定串形：与 `preflight/review_independence.describe_target` **同一形态**
#: （`endpoint/model_name`）。本模块不 import 那个模块（分层：preflight 属编译期，
#: 评审聚合属运行期），但判据面钉住两者形态一致。
Target = str


@dataclass(frozen=True, slots=True)
class PanelVerdict:
    """一条评审小组的**建议性**结论（不参与 `Decision`）。"""

    #: 参与投票的 finding 数（**不含**被点名为无法投票的那些）。
    voters: int
    #: 票数（`verdict` → 计数），键序稳定。
    votes: dict[str, int] = field(default_factory=dict)
    #: 聚合结论：唯一最高票的那个取值；平票 / 无票 ⇒ `None`。
    advisory: str | None = None
    #: 少数意见（未被采纳的那些票），逐条 `reviewer_id:verdict`。
    dissent: tuple[str, ...] = ()
    #: 无法投票的 finding（逐条点名理由）。
    ineligible: tuple[str, ...] = ()
    #: 评审者之间的**执行目标**集合（去重后的 `endpoint/model_name`）。
    targets: tuple[Target, ...] = ()
    #: 是否**独立复核**：参与者 ≥ 2 且**每个**参与者的目标互不相同，且**没有**无法归因的。
    independent: bool = False
    #: 独立性不成立的理由（逐条点名）；`independent=True` 时为空。
    independence_notes: tuple[str, ...] = ()

    @property
    def decided(self) -> bool:
        """有明确多数结论（不是平票、不是无票）。"""
        return self.advisory is not None

    def as_payload(self) -> dict[str, object]:
        """读面形态（稳定键序；`dict` 便于落库与比对）。"""
        return {
            "voters": self.voters,
            "votes": dict(sorted(self.votes.items())),
            "advisory": self.advisory,
            "dissent": list(self.dissent),
            "ineligible": list(self.ineligible),
            "targets": list(self.targets),
            "independent": self.independent,
            "independence_notes": list(self.independence_notes),
        }


def review_target(*, endpoint_id: str | None, model_name: str | None) -> Target | None:
    """`(endpoint, model_name)` → 稳定串形；任一缺失 ⇒ `None`（**不**拼半个目标）。"""
    if not endpoint_id or not model_name:
        return None
    return f"{endpoint_id}/{model_name}"


def _eligible(finding: ReviewFinding) -> str | None:
    """该 finding 能否投票：不能 ⇒ 返回**点名理由**。"""
    if not finding.verdict.strip():
        return f"{finding.id}: verdict is empty"
    if finding.reviewer_model is None:
        return f"{finding.id}: reviewer model is not recorded (cannot attribute this verdict)"
    return None


def aggregate_panel(findings: Sequence[ReviewFinding]) -> PanelVerdict | None:
    """把一个阶段上的多份评审结论聚合成**一条建议性**结论。

    **少于两份 ⇒ `None`**（单评审不聚合：既有读面与判词逐字不变 —— 那是本 GOAL 的
    零回归边界，不是遗漏）。
    """
    if len(findings) < 2:
        return None
    votes: dict[str, int] = {}
    ineligible: list[str] = []
    voters: list[ReviewFinding] = []
    for finding in findings:
        reason = _eligible(finding)
        if reason is not None:
            ineligible.append(reason)
            continue
        voters.append(finding)
        key = finding.verdict.strip().upper()
        votes[key] = votes.get(key, 0) + 1
    targets = sorted({
        str(item.reviewer_model) for item in voters if item.reviewer_model is not None
    })
    notes: list[str] = []
    if len(voters) < 2:
        notes.append(f"only {len(voters)} attributable vote(s); independence cannot be established")
    if len(targets) != len(voters):
        notes.append(
            "at least two reviewers share the same target "
            f"({', '.join(targets)}); reviewing your own model is not an independent panel"
        )
    notes.extend(ineligible)
    advisory = _advisory(votes)
    dissent = tuple(
        f"{_speaker(item)}:{item.verdict.strip().upper()}"
        for item in sorted(voters, key=_speaker)
        if advisory is not None and item.verdict.strip().upper() != advisory
    )
    return PanelVerdict(
        voters=len(voters),
        votes=dict(sorted(votes.items())),
        advisory=advisory,
        dissent=dissent,
        ineligible=tuple(ineligible),
        targets=tuple(targets),
        independent=not notes,
        independence_notes=tuple(notes),
    )


def _speaker(finding: ReviewFinding) -> str:
    """这条 finding 的**发言者**（用于少数意见的可读点名）。

    `ReviewFinding` 没有 `reviewer_id`；它的作者面是 `reviewed_by`（`gate:<agent id>`，
    由验收门填）。缺失时回落到 finding id —— 保证 dissent **总可读**，不伪造身份。
    """
    return finding.reviewed_by or finding.id


def _advisory(votes: dict[str, int]) -> str | None:
    """唯一最高票 ⇒ 该取值；**平票或无票 ⇒ `None`**（不猜，与 `_majority_verdict` 同形）。"""
    if not votes:
        return None
    ranked = sorted(votes.items(), key=lambda item: (-item[1], item[0]))
    top = ranked[0][1]
    if sum(1 for _, count in ranked if count == top) > 1:
        return None
    return ranked[0][0]


__all__ = [
    "PanelVerdict",
    "Target",
    "aggregate_panel",
    "review_target",
]
