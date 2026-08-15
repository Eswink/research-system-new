"""M11 Reviewer 契约与 LLM 实现（judgment 不是 truth，失败语义结构化）。

约束：
- Reviewer 输入是真实 evaluation material（case rubric + material
  reference），不是被评对象自述的成功摘要；
- 评测设施失败（timeout/malformed/unavailable）→ ReviewerFinding.failure
  结构化记录，绝不映射为被评对象 FAIL/PASS；
- Reviewer 判断不得修改 Evidence/Claim truth（本模块无任何写路径）；
- 确定性可验证的事实不得进入 Reviewer（由 deterministic scorers 先行）。
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, runtime_checkable

from packages.application.ports.credential_resolver import SecretValue
from packages.application.ports.model_gateway import (
    CompletionRequest,
    ModelGateway,
)
from packages.domain.eval_result import (
    ReviewerFinding,
    ReviewerVerdict,
)
from packages.domain.eval_spec import RubricSpec
from packages.domain.models import LLMEndpoint

_VERDICT_TOKENS = {
    "PASS": ReviewerVerdict.PASS,
    "FAIL": ReviewerVerdict.FAIL,
    "AMBIGUOUS": ReviewerVerdict.AMBIGUOUS,
}


@dataclass(frozen=True, slots=True)
class ReviewMaterial:
    """一次 rubric 维度评审的输入：只含引用与规格，不含 secret。"""

    case_id: str
    rubric: RubricSpec
    material_ref: str
    system_version: str


@dataclass(frozen=True, slots=True)
class ReviewAssignment:
    reviewer_id: str
    material: ReviewMaterial


@runtime_checkable
class Reviewer(Protocol):
    """评审者契约：material → ReviewerFinding（永不抛被评对象语义）。"""

    def review(self, assignment: ReviewAssignment) -> ReviewerFinding: ...


def _judgment_verdict(token: str) -> ReviewerVerdict | None:
    for key, verdict in _VERDICT_TOKENS.items():
        if key in token:
            return verdict
    return None


def _parse_verdict(content: str) -> ReviewerVerdict | None:
    upper = content.upper()
    verdict = _judgment_verdict(upper)
    if verdict is None:
        return None
    return verdict


@dataclass(frozen=True, slots=True)
class LlmReviewer:
    """经 ModelGateway Port 的 LLM 评审实现（真实 LLM 仅手动/显式运行）。

    输入只传 rubric + material reference；不传 secret、不传完整敏感内容；
    返回的模型名与采样参数记入 finding（模型同名漂移可见）。
    """

    reviewer_id: str
    gateway: ModelGateway
    endpoint: LLMEndpoint
    credential: SecretValue
    model_id: str
    temperature: Decimal = Decimal("0")

    def review(self, assignment: ReviewAssignment) -> ReviewerFinding:
        material = assignment.material
        rubric = material.rubric
        prompt = (
            f"Case: {material.case_id}\n"
            f"Material reference: {material.material_ref}\n"
            f"Rubric dimension: {rubric.dimension}\n"
            f"Rubric description: {rubric.description}\n"
            f"Scale: {rubric.scale[0]}..{rubric.scale[1]}\n"
            "Answer with exactly one verdict token: PASS, FAIL or AMBIGUOUS, "
            "followed by a one-line rationale."
        )
        try:
            result = self.gateway.complete(
                self.endpoint,
                self.credential,
                CompletionRequest(
                    model=self.model_id,
                    messages=[{"role": "user", "content": prompt}],
                ),
            )
        except Exception as exc:  # noqa: BLE001 - 设施故障不得判被评对象
            return self._failure(material, f"unavailable: {type(exc).__name__}")
        content = result.content
        if content is None:
            return self._failure(material, "malformed: empty response")
        verdict = _parse_verdict(content)
        if verdict is None:
            return self._failure(material, f"malformed: no verdict token in {content!r}")
        model_identity = result.returned_model_name or self.model_id
        return ReviewerFinding(
            reviewer_id=self.reviewer_id,
            model_identity=model_identity,
            rubric_id=rubric.id,
            verdict=verdict,
            rationale=content,
            temperature=str(self.temperature),
            repetitions=1,
        )

    def _failure(self, material: ReviewMaterial, reason: str) -> ReviewerFinding:
        return ReviewerFinding(
            reviewer_id=self.reviewer_id,
            model_identity=self.model_id,
            rubric_id=material.rubric.id,
            verdict=ReviewerVerdict.AMBIGUOUS,
            rationale="",
            failure=reason,
            temperature=str(self.temperature),
            repetitions=1,
        )
