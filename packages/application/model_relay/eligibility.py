"""ModelEligibilityPolicy：模型能力硬门槛纯决策。

判定规则（docs/architecture/MODEL_COMPATIBILITY.md §4）：
- 硬能力必须全部以 SUPPORTED 满足；UNKNOWN/DEGRADED 视为不满足；
- TOOL_CALLING_EMULATED 仅在显式批准时视为满足 TOOL_CALLING 要求。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.domain.enums import CapabilityStatus, ModelCapability
from packages.domain.models import CapabilityAssertion, ModelDefinition

TOOL_CALLING_NATIVE = ModelCapability.TOOL_CALLING_NATIVE
TOOL_CALLING_EMULATED = ModelCapability.TOOL_CALLING_EMULATED


@dataclass(frozen=True, slots=True)
class EligibilityDecision:
    """决策结果；missing 列出不满足的硬能力。"""

    allowed: bool
    missing_capabilities: tuple[ModelCapability, ...] = ()
    reason: str = ""


def decide_eligibility(
    model: ModelDefinition,
    hard_capabilities: set[ModelCapability],
    *,
    allow_tool_calling_emulated: bool = False,
) -> EligibilityDecision:
    """判定模型是否满足全部硬能力。

    单项能力的 SUPPORTED 判定：
    - 硬能力不在 capabilities 中 → 不满足；
    - TOOL_CALLING_NATIVE 只在显式支持时满足；
    - TOOL_CALLING_EMULATED 作为 TOOL_CALLING_NATIVE 的替代，
      仅当 allow_tool_calling_emulated=True 且显式 SUPPORTED 时满足；
    - 其余能力必须 status=SUPPORTED 才满足。
    """

    def _satisfies(capability: ModelCapability) -> bool:
        assertion: CapabilityAssertion | None = model.capabilities.get(capability)
        if assertion is not None and assertion.status is CapabilityStatus.SUPPORTED:
            if capability is TOOL_CALLING_NATIVE or capability is TOOL_CALLING_EMULATED:
                return capability is TOOL_CALLING_NATIVE or allow_tool_calling_emulated
            return True
        # TOOL_CALLING_NATIVE 硬要求允许经批准的 emulated 替代
        if capability is TOOL_CALLING_NATIVE and allow_tool_calling_emulated:
            emulated = model.capabilities.get(TOOL_CALLING_EMULATED)
            if emulated is not None and emulated.status is CapabilityStatus.SUPPORTED:
                return True
        return False

    missing = tuple(
        capability
        for capability in sorted(hard_capabilities, key=lambda item: item.value)
        if not _satisfies(capability)
    )
    if not missing:
        return EligibilityDecision(allowed=True, reason="all hard capabilities satisfied")
    return EligibilityDecision(
        allowed=False,
        missing_capabilities=missing,
        reason=f"missing hard capabilities: {[item.value for item in missing]}",
    )
