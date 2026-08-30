"""M11 Reviewer 失败语义测试：timeout/malformed/unavailable、独立性、真实输入。"""

from __future__ import annotations

from adapters.fakes.model_gateway import FakeModelGateway, FakeModelGatewayOptions
from adapters.fakes.reviewer import FakeReviewer
from packages.application.evaluation.reviewer import (
    LlmReviewer,
    ReviewAssignment,
    ReviewMaterial,
)
from packages.application.ports.credential_resolver import SecretValue
from packages.application.ports.model_gateway import (
    CompletionRequest,
    CompletionResult,
    ModelsListResult,
)
from packages.domain.eval_result import ReviewerVerdict
from packages.domain.eval_spec import RubricSpec
from packages.domain.models import EndpointProbeSnapshot, LLMEndpoint

_RUBRIC = RubricSpec("soundness", "soundness", "is the answer sound?")


def _material(case_id: str = "case-1") -> ReviewMaterial:
    return ReviewMaterial(
        case_id=case_id,
        rubric=_RUBRIC,
        material_ref="artifact://case-1/main",
        system_version="0.4.0",
    )


def _assignment(case_id: str = "case-1") -> ReviewAssignment:
    return ReviewAssignment(reviewer_id="r1", material=_material(case_id))


def _endpoint() -> LLMEndpoint:
    return LLMEndpoint(
        id="ep-1",
        name="fake",
        protocol="OPENAI_COMPATIBLE",
        base_url="https://fake.local/v1",
        credential_ref="cred-1",
    )


class _ScriptedGateway:
    """complete 返回预设 content 的最小 ModelGateway 实现。"""

    def __init__(self, content: str | None) -> None:
        self._content = content

    def list_models(self, endpoint: LLMEndpoint, credential: SecretValue) -> ModelsListResult:
        return ModelsListResult(model_ids=("scripted-model",))

    def complete(
        self,
        endpoint: LLMEndpoint,
        credential: SecretValue,
        request: CompletionRequest,
    ) -> CompletionResult:
        return CompletionResult(
            content=self._content,
            returned_model_name="scripted-model",
        )

    def probe_endpoint(
        self,
        endpoint: LLMEndpoint,
        credential: SecretValue,
        request: CompletionRequest,
    ) -> EndpointProbeSnapshot:
        return EndpointProbeSnapshot(ok=True)

    def probe_connectivity(
        self, endpoint: LLMEndpoint, credential: SecretValue
    ) -> EndpointProbeSnapshot:
        return EndpointProbeSnapshot(ok=True)


def test_llm_reviewer_parses_verdict_tokens() -> None:
    gateway = _ScriptedGateway("PASS because the answer is sound")
    reviewer = LlmReviewer(
        reviewer_id="r1",
        gateway=gateway,
        endpoint=_endpoint(),
        credential=SecretValue("secret"),
        model_id="fake-model",
    )
    finding = reviewer.review(_assignment())
    assert finding.verdict is ReviewerVerdict.PASS
    assert finding.model_identity == "scripted-model"
    assert finding.temperature == "0"
    assert finding.repetitions == 1


def test_llm_reviewer_malformed_output_is_infra_failure() -> None:
    reviewer = LlmReviewer(
        reviewer_id="r1",
        gateway=_ScriptedGateway("here is a long essay with no verdict token"),
        endpoint=_endpoint(),
        credential=SecretValue("secret"),
        model_id="fake-model",
    )
    finding = reviewer.review(_assignment())
    assert finding.failure is not None
    assert "malformed" in finding.failure


def test_llm_reviewer_empty_content_is_infra_failure() -> None:
    reviewer = LlmReviewer(
        reviewer_id="r1",
        gateway=_ScriptedGateway(None),
        endpoint=_endpoint(),
        credential=SecretValue("secret"),
        model_id="fake-model",
    )
    finding = reviewer.review(_assignment())
    assert finding.failure is not None
    assert "malformed" in finding.failure


def test_llm_reviewer_unavailable_model_is_infra_failure() -> None:
    gateway = FakeModelGateway(FakeModelGatewayOptions(fail_timeout=True))
    reviewer = LlmReviewer(
        reviewer_id="r1",
        gateway=gateway,
        endpoint=_endpoint(),
        credential=SecretValue("secret"),
        model_id="fake-model",
    )
    finding = reviewer.review(_assignment())
    assert finding.failure is not None
    assert "unavailable" in finding.failure


def test_reviewer_failure_never_maps_to_subject_pass_or_fail() -> None:
    # 评审设施故障必须保持 AMBIGUOUS + failure 字段；不得产生 PASS/FAIL
    reviewer = FakeReviewer(
        reviewer_id="r1",
        failure="timeout",
        verdict=ReviewerVerdict.AMBIGUOUS,
    )
    finding = reviewer.review(_assignment())
    assert finding.failure == "timeout"
    assert finding.verdict is ReviewerVerdict.AMBIGUOUS


def test_reviewer_material_carries_no_secrets() -> None:
    # 结构断言：ReviewMaterial 只有引用/rubric 字段，没有凭据或内容通道。
    # （字符串自比型断言对固定字面量恒真，无判别力——改用字段级检查。）
    from dataclasses import fields

    names = {field.name for field in fields(ReviewMaterial)}
    allowed = {"case_id", "rubric", "material_ref", "system_version"}
    assert names <= allowed, f"ReviewMaterial 出现未审计字段: {names - allowed}"
    assert "credential" not in names and "secret" not in names
    assert "expected" not in names and "score" not in names


def test_reviewer_judgment_does_not_mutate_material() -> None:
    material = _material()
    reviewer = FakeReviewer(reviewer_id="r1", verdict=ReviewerVerdict.FAIL)
    before = str(material)
    reviewer.review(ReviewAssignment(reviewer_id="r1", material=material))
    assert str(material) == before


def test_reviewer_cannot_receive_self_reported_score() -> None:
    # 被评对象自报分数不进入评审输入：ReviewMaterial 结构上没有该字段，
    # 传入未知关键字必须构造失败（结构上不可表达，非文档约定）。
    import pytest

    with pytest.raises(TypeError):
        ReviewMaterial(  # type: ignore[call-arg]
            case_id="case-1",
            rubric=_RUBRIC,
            material_ref="artifact://case-1/main",
            system_version="0.4.0",
            self_reported_score=1.0,
        )
