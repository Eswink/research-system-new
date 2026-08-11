"""Fallback 决策测试。"""

from __future__ import annotations

from packages.application.model_relay.fallback import FallbackContext, plan_fallback
from packages.domain.enums import CapabilitySource, CapabilityStatus, ModelCapability
from packages.domain.models import CapabilityAssertion, ModelDefinition

CHAT = ModelCapability.CHAT
TOOL_NATIVE = ModelCapability.TOOL_CALLING_NATIVE


def _model(model_id: str, capabilities: set[ModelCapability]) -> ModelDefinition:
    assertions = {
        cap: CapabilityAssertion(
            status=CapabilityStatus.SUPPORTED, confidence=1.0, source=CapabilitySource.USER_DECLARED
        )
        for cap in capabilities
    }
    return ModelDefinition(
        id=model_id, endpoint_id="main", model_name=model_id, capabilities=assertions
    )


PRIMARY = _model("research_alpha", {CHAT, TOOL_NATIVE})
ELIGIBLE = _model("coding_beta", {CHAT, TOOL_NATIVE})
INELIGIBLE = _model("reviewer_gamma", {CHAT})

HARD_CAPS: set[ModelCapability] = {CHAT, TOOL_NATIVE}


def _context(
    *,
    hard_caps: set[ModelCapability] = HARD_CAPS,
    failure_reason: str = "MODEL_RATE_LIMIT_EXHAUSTED",
    task_ref: str | None = None,
    manifest_policy: str | None = None,
    allow_session_switch: bool = False,
) -> FallbackContext:
    return FallbackContext(
        primary_model=PRIMARY,
        hard_capabilities=hard_caps,
        failure_reason=failure_reason,
        task_ref=task_ref,
        manifest_policy=manifest_policy,
        allow_session_switch=allow_session_switch,
    )


class TestPlanFallback:
    def test_eligible_candidate_selected(self) -> None:
        plan = plan_fallback(context=_context(), candidates=[ELIGIBLE])
        assert plan.should_fallback
        assert plan.target_model_id == "coding_beta"
        assert plan.audits[0].from_model == "research_alpha"
        assert plan.audits[0].to_model == "coding_beta"
        assert plan.audits[0].session_switched is False

    def test_ineligible_candidate_skipped_with_audit(self) -> None:
        plan = plan_fallback(context=_context(), candidates=[INELIGIBLE])
        assert not plan.should_fallback
        assert plan.target_model_id is None
        assert plan.audits[0].to_model == "reviewer_gamma"

    def test_primary_not_considered_as_fallback(self) -> None:
        plan = plan_fallback(context=_context(), candidates=[PRIMARY, ELIGIBLE])
        assert plan.should_fallback
        assert plan.target_model_id == "coding_beta"

    def test_no_candidates_returns_no_fallback(self) -> None:
        plan = plan_fallback(context=_context(), candidates=[])
        assert not plan.should_fallback
        assert plan.audits == ()

    def test_audit_carries_task_and_policy_refs(self) -> None:
        plan = plan_fallback(
            context=_context(
                task_ref="research-task:example-001", manifest_policy="fallback_allowed"
            ),
            candidates=[ELIGIBLE],
        )
        record = plan.audits[0]
        assert record.task_ref == "research-task:example-001"
        assert record.manifest_policy == "fallback_allowed"

    def test_session_switch_flag_carried(self) -> None:
        plan = plan_fallback(context=_context(allow_session_switch=True), candidates=[ELIGIBLE])
        assert plan.audits[0].session_switched is True
