"""ModelEligibilityPolicy 纯决策测试。

覆盖：硬能力全满足、UNKNOWN/DEGRADED 视为不满足、TOOL_CALLING_EMULATED
仅在显式批准时满足、缺失能力枚举。
"""

from __future__ import annotations

from packages.application.model_relay.eligibility import decide_eligibility
from packages.domain.enums import CapabilitySource, CapabilityStatus, ModelCapability
from packages.domain.models import CapabilityAssertion, ModelDefinition

CHAT = ModelCapability.CHAT
STREAMING = ModelCapability.STREAMING
TOOL_NATIVE = ModelCapability.TOOL_CALLING_NATIVE
TOOL_EMULATED = ModelCapability.TOOL_CALLING_EMULATED
STRUCTURED = ModelCapability.STRUCTURED_OUTPUT_NATIVE


def _model(capabilities: dict[ModelCapability, CapabilityAssertion]) -> ModelDefinition:
    return ModelDefinition(
        id="m1", endpoint_id="e1", model_name="model-alpha", capabilities=capabilities
    )


def _supported(capability: ModelCapability) -> CapabilityAssertion:
    return CapabilityAssertion(
        status=CapabilityStatus.SUPPORTED, confidence=1.0, source=CapabilitySource.USER_DECLARED
    )


def _unknown(capability: ModelCapability) -> CapabilityAssertion:
    return CapabilityAssertion(
        status=CapabilityStatus.UNKNOWN, confidence=0.0, source=CapabilitySource.USER_DECLARED
    )


def _degraded(capability: ModelCapability) -> CapabilityAssertion:
    return CapabilityAssertion(
        status=CapabilityStatus.DEGRADED, confidence=0.3, source=CapabilitySource.USER_DECLARED
    )


class TestDecideEligibility:
    def test_all_hard_capabilities_satisfied_allows(self) -> None:
        model = _model({CHAT: _supported(CHAT), TOOL_NATIVE: _supported(TOOL_NATIVE)})
        decision = decide_eligibility(model, {CHAT, TOOL_NATIVE})
        assert decision.allowed
        assert decision.missing_capabilities == ()

    def test_missing_capability_rejects(self) -> None:
        model = _model({CHAT: _supported(CHAT)})
        decision = decide_eligibility(model, {CHAT, TOOL_NATIVE})
        assert not decision.allowed
        assert decision.missing_capabilities == (TOOL_NATIVE,)

    def test_unknown_capability_counts_as_missing(self) -> None:
        model = _model({CHAT: _supported(CHAT), TOOL_NATIVE: _unknown(TOOL_NATIVE)})
        decision = decide_eligibility(model, {CHAT, TOOL_NATIVE})
        assert not decision.allowed
        assert TOOL_NATIVE in decision.missing_capabilities

    def test_degraded_capability_counts_as_missing(self) -> None:
        model = _model({CHAT: _supported(CHAT), TOOL_NATIVE: _degraded(TOOL_NATIVE)})
        decision = decide_eligibility(model, {CHAT, TOOL_NATIVE})
        assert not decision.allowed
        assert TOOL_NATIVE in decision.missing_capabilities

    def test_emulated_tool_calling_denied_by_default(self) -> None:
        model = _model({CHAT: _supported(CHAT), TOOL_EMULATED: _supported(TOOL_EMULATED)})
        decision = decide_eligibility(model, {TOOL_NATIVE})
        assert not decision.allowed

    def test_emulated_tool_calling_allowed_when_approved(self) -> None:
        model = _model({CHAT: _supported(CHAT), TOOL_EMULATED: _supported(TOOL_EMULATED)})
        decision = decide_eligibility(model, {TOOL_NATIVE}, allow_tool_calling_emulated=True)
        assert decision.allowed

    def test_structured_output_supported(self) -> None:
        model = _model({CHAT: _supported(CHAT), STRUCTURED: _supported(STRUCTURED)})
        decision = decide_eligibility(model, {CHAT, STRUCTURED})
        assert decision.allowed

    def test_reason_reports_missing(self) -> None:
        model = _model({CHAT: _supported(CHAT)})
        decision = decide_eligibility(model, {CHAT, STREAMING})
        assert "STREAMING" in decision.reason
