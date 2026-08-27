"""ApprovalStore Port：待决审批的规范记录与存储（M13-R1 引入）。

职责：Policy 要求审批（REQUIRE_APPROVAL）的待决记录持久化；
裁决规则（If-Match/状态机）在 application/API 编排层（本 Port 只做
存储语义：register/list/get/replace）。
PendingApproval 的等价定义（ApprovalRecord）从 entry 层下沉到 Port，
使 adapter 实现不依赖 services.api（依赖方向 adapter → application → domain）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class ApprovalSpec:
    """审批注册输入（参数对象）。"""

    run_id: str
    action: str
    risk: str
    context: str
    policy_source: str
    requested_event_id: str


@dataclass(frozen=True, slots=True)
class ApprovalRecord:
    """一条待决审批记录（事件投影的轻量物化）。"""

    id: str
    run_id: str
    action: str
    risk: str
    context: str
    policy_source: str
    requested_event_id: str
    status: str = "PENDING"
    version: str = ""

    def with_decision(self, decision: str) -> ApprovalRecord:
        """裁决后的新实例（旧实例保留历史；version 变化供 If-Match）。"""
        import uuid

        return ApprovalRecord(
            id=self.id,
            run_id=self.run_id,
            action=self.action,
            risk=self.risk,
            context=self.context,
            policy_source=self.policy_source,
            requested_event_id=self.requested_event_id,
            status="APPROVED" if decision == "approve" else "DENIED",
            version=f"sha256:{uuid.uuid4().hex}",
        )


@runtime_checkable
class ApprovalStore(Protocol):
    """审批存储；CRUD 语义由实现保证。"""

    def register(self, spec: ApprovalSpec) -> ApprovalRecord: ...

    def list_pending(self) -> tuple[ApprovalRecord, ...]: ...

    def list_for_run(self, run_id: str) -> tuple[ApprovalRecord, ...]: ...

    def get(self, approval_id: str) -> ApprovalRecord | None: ...

    def replace(self, approval: ApprovalRecord) -> None: ...
