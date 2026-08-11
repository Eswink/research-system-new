"""Fallback 决策与审计记录。

规则（docs/integration/MODEL_GATEWAY.md §5）：
- Fallback 模型必须满足 Role 硬能力；
- 受 budget/policy 约束；
- Session 中途默认不切换模型（只记录决策与候选，执行在 M6/M7）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from packages.application.model_relay.eligibility import decide_eligibility
from packages.domain.enums import ModelCapability
from packages.domain.models import FallbackAuditRecord, ModelDefinition


@dataclass(frozen=True, slots=True)
class FallbackContext:
    """Fallback 决策上下文（参数对象，控制函数签名 <= 5）。"""

    primary_model: ModelDefinition
    hard_capabilities: set[ModelCapability]
    failure_reason: str
    task_ref: str | None = None
    manifest_policy: str | None = None
    allow_session_switch: bool = False
    occurred_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class FallbackPlan:
    """Fallback 决策结果。"""

    should_fallback: bool
    target_model_id: str | None = None
    reason: str = ""
    audits: tuple[FallbackAuditRecord, ...] = field(default_factory=tuple)


def _reject_audit(context: FallbackContext, candidate: ModelDefinition) -> FallbackAuditRecord:
    return FallbackAuditRecord(
        from_model=context.primary_model.id,
        to_model=candidate.id,
        reason=f"candidate lacks hard capabilities: {context.failure_reason}",
        occurred_at=context.occurred_at or datetime.now(timezone.utc),
        task_ref=context.task_ref,
        manifest_policy=context.manifest_policy,
        session_switched=False,
    )


def _accept_audit(context: FallbackContext, candidate: ModelDefinition) -> FallbackAuditRecord:
    return FallbackAuditRecord(
        from_model=context.primary_model.id,
        to_model=candidate.id,
        reason=context.failure_reason,
        occurred_at=context.occurred_at or datetime.now(timezone.utc),
        task_ref=context.task_ref,
        manifest_policy=context.manifest_policy,
        session_switched=context.allow_session_switch,
    )


def plan_fallback(
    *,
    context: FallbackContext,
    candidates: list[ModelDefinition],
) -> FallbackPlan:
    """选择满足硬能力且非 primary 的候选模型。

    不满足硬能力的候选被跳过并记录审计；无可用候选时返回
    should_fallback=False。
    """
    audits: list[FallbackAuditRecord] = []
    for candidate in candidates:
        if candidate.id == context.primary_model.id:
            continue
        decision = decide_eligibility(candidate, set(context.hard_capabilities))
        if not decision.allowed:
            audits.append(_reject_audit(context, candidate))
            continue
        audits.append(_accept_audit(context, candidate))
        return FallbackPlan(
            should_fallback=True,
            target_model_id=candidate.id,
            reason=context.failure_reason,
            audits=tuple(audits),
        )
    return FallbackPlan(
        should_fallback=False, reason="no eligible fallback candidate", audits=tuple(audits)
    )
