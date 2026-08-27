"""Control Plane 审批注册表与裁决（M13）。

语义（M13 DoD 7）：审批是 Policy 要求（PolicyEvaluator REQUIRE_APPROVAL），
不是 UI 决定。hidden button != authorization：即使直接调用 API，
decide 仍校验：
- approval 存在且未决（duplicate decide → 409）；
- If-Match version 匹配（stale decision → 412）；
- run 处于 WAITING_FOR_APPROVAL（非法状态机 → 409）；
- 后端 PolicyEvaluator 仍要求审批（policy 未放行 → deny）。

裁决通过正式事件（approval.decided）与 Run 状态机迁移（APPROVAL_GRANTED /
APPROVAL_REJECTED）落审计。M14 PostgreSQL canonical state 落地后本注册表
由持久化实现替换（ApprovalStore Port 不变）。

M13-R1：ApprovalSpec/ApprovalRecord 定义下沉到
packages/application/ports/approval_store.py（adapter 不依赖 entry 层）；
PendingApproval 保留为别名（既有测试兼容）。
"""

from __future__ import annotations

import uuid

from packages.application.ports.approval_store import (
    ApprovalRecord,
    ApprovalSpec,
    ApprovalStore,
)
from packages.domain.core import Timestamp
from packages.domain.events import EventEnvelope, EventType, digest_of_payload
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
from services.api.errors import ApiError

APPROVAL_VERSION_DIGEST = "sha256:" + "0" * 64  # M13 内存版恒为 0 基线（M14 换语义版本）

PendingApproval = ApprovalRecord

__all__ = [
    "APPROVAL_VERSION_DIGEST",
    "ApprovalRecord",
    "ApprovalRegistry",
    "ApprovalSpec",
    "ApprovalStore",
    "PendingApproval",
    "approval_event_payload",
    "build_approval_event",
    "decide_approval",
]


class ApprovalRegistry(ApprovalStore):
    """内存审批注册表（ApprovalStore Port 实现；M14 换持久化实现）。"""

    def __init__(self) -> None:
        self._approvals: dict[str, ApprovalRecord] = {}
        self._by_run: dict[str, list[str]] = {}

    def register(self, spec: ApprovalSpec) -> ApprovalRecord:
        approval = ApprovalRecord(
            id=uuid.uuid4().hex,
            run_id=spec.run_id,
            action=spec.action,
            risk=spec.risk,
            context=spec.context,
            policy_source=spec.policy_source,
            requested_event_id=spec.requested_event_id,
        )
        self._approvals[approval.id] = approval
        self._by_run.setdefault(spec.run_id, []).append(approval.id)
        return approval

    def list_pending(self) -> tuple[ApprovalRecord, ...]:
        return tuple(
            approval for approval in self._approvals.values() if approval.status == "PENDING"
        )

    def list_for_run(self, run_id: str) -> tuple[ApprovalRecord, ...]:
        return tuple(self._approvals[approval_id] for approval_id in self._by_run.get(run_id, ()))

    def get(self, approval_id: str) -> ApprovalRecord | None:
        return self._approvals.get(approval_id)

    def replace(self, approval: ApprovalRecord) -> None:
        self._approvals[approval.id] = approval


def decide_approval(
    *,
    registry: ApprovalStore,
    approval_id: str,
    decision: str,
    if_match: str | None,
    run: ResearchRun,
) -> ApprovalRecord:
    """后端裁决：hidden button != authorization（直接调 API 同样执行规则）。"""
    approval = registry.get(approval_id)
    if approval is None:
        raise ApiError(404, "Not Found", f"approval not found: {approval_id}")
    if approval.status != "PENDING":
        raise ApiError(409, "Approval Already Decided", f"approval is {approval.status}")
    if approval.run_id != run.id.value:
        raise ApiError(409, "Approval Run Mismatch", "approval does not belong to this run")
    if run.state != ResearchRunState.State.WAITING_FOR_APPROVAL:
        raise ApiError(
            409,
            "Invalid Transition",
            f"cannot decide approval in run state {run.state}",
        )
    if if_match is None:
        raise ApiError(428, "Precondition Required", "If-Match header is required for decision")
    if if_match != "*" and if_match != approval.version:
        raise ApiError(412, "Precondition Failed", "approval version mismatch")
    if decision not in ("approve", "deny"):
        raise ApiError(422, "Invalid Decision", "decision must be 'approve' or 'deny'")
    decided = approval.with_decision(decision)
    registry.replace(decided)
    return decided


def approval_event_payload(approval: ApprovalRecord) -> dict[str, object]:
    """裁决事件的 payload（审计投影；不含 secret）。"""
    return {
        "approval_id": approval.id,
        "run_id": approval.run_id,
        "action": approval.action,
        "risk": approval.risk,
        "status": approval.status,
        "policy_source": approval.policy_source,
        "requested_event_id": approval.requested_event_id,
    }


def build_approval_event(
    approval: ApprovalRecord,
    *,
    actor: str,
) -> EventEnvelope:
    """构建 approval.decided 正式事件（进 outbox 审计）。"""
    payload = approval_event_payload(approval)
    return EventEnvelope(
        event_id=uuid.uuid4().hex,
        event_type=EventType.APPROVAL_DECIDED,
        schema_version="0.4.0",
        occurred_at=Timestamp.now(),
        actor=actor,
        scope="project",
        payload=payload,
        payload_digest=digest_of_payload(payload),
        run_id=approval.run_id,
        trace_id=f"approval-{approval.id}",
    )
