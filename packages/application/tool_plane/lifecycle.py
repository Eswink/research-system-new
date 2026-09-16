"""ToolPack lifecycle use case：install / approve-update / revoke（ADR-0019）。

供应链验证（digest 校验）在安装门禁内：manifest.digest 必须与内容
重算一致；更新若扩张权限（requested_capabilities / network_domains /
credentials 差集）**不立即生效**——登记为待批准更新，`approve_update`
通过 policy 后才替换；revoke 记录原因、清空待批准更新并发布领域事件。

诚实边界：digest 一致是控制面**自己重算**出来的（不是采信调用方写的字面量），
但控制面不取 pack 的远端交付物，因此它证明的是"提交的内容与声明的 pin 自洽"，
不是"pin 与上游仓库实际内容一致"——后者需要远端取证，不在本层。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from packages.application.ports.errors import InvalidInputError, PermanentPortError
from packages.application.ports.event_publisher import EventPublisher
from packages.application.ports.policy_evaluator import PolicyEvaluator, PolicyRequest
from packages.application.ports.tool_pack_store import ToolPackRecord, ToolPackStore
from packages.domain.core import Timestamp
from packages.domain.enums import (
    CredentialScope,
    FailureCategory,
    PolicyDecision,
    ToolPackState,
)
from packages.domain.events import (
    EventEnvelope,
    EventType,
    digest_of_payload,
)
from packages.domain.tools import ToolPackManifest

_INSTALL_CAPABILITY = "tool_pack.install"
_UPDATE_CAPABILITY = "tool_pack.update"
_REVOKE_CAPABILITY = "tool_pack.revoke"


@dataclass(frozen=True, slots=True)
class PermissionDiff:
    added_capabilities: tuple[str, ...] = ()
    added_network_domains: tuple[str, ...] = ()
    added_credentials: tuple[str, ...] = ()

    @property
    def is_empty(self) -> bool:
        return not (self.added_capabilities or self.added_network_domains or self.added_credentials)


def permission_diff(old: ToolPackManifest, new: ToolPackManifest) -> PermissionDiff:
    return PermissionDiff(
        added_capabilities=tuple(
            sorted(set(new.requested_capabilities) - set(old.requested_capabilities))
        ),
        added_network_domains=tuple(sorted(set(new.network_domains) - set(old.network_domains))),
        added_credentials=tuple(
            sorted({c.name for c in new.credentials} - {c.name for c in old.credentials})
        ),
    )


def _require_decision(
    evaluator: PolicyEvaluator,
    actor: str,
    capability: str,
    pack_id: str,
) -> None:
    decision = evaluator.evaluate(
        PolicyRequest(actor=actor, capability=capability, resource=pack_id)
    ).decision
    if decision is PolicyDecision.DENY:
        raise PermanentPortError(
            f"policy denied capability {capability} for pack {pack_id}",
            failure_category=FailureCategory.POLICY_DENIED,
        )


def _publish(
    publisher: EventPublisher,
    event_type: EventType,
    pack_id: str,
    actor: str,
    extra: dict[str, object] | None = None,
) -> None:
    payload: dict[str, object] = {"pack_id": pack_id, **(extra or {})}
    publisher.publish(
        EventEnvelope(
            event_id=f"m8:{event_type.value}:{pack_id}",
            event_type=event_type,
            schema_version="1",
            occurred_at=Timestamp.now(),
            actor=actor,
            scope=f"tool_pack:{pack_id}",
            payload=payload,
            payload_digest=digest_of_payload(payload),
        )
    )


def _verify_supply_chain(manifest: ToolPackManifest) -> None:
    if not manifest.verify_content_digest():
        raise PermanentPortError(
            f"tool pack {manifest.id} digest mismatch: content does not match declared digest",
            failure_category=FailureCategory.VALIDATION_FAILURE,
        )
    for credential in manifest.credentials:
        if credential.required and credential.scope is not CredentialScope.TOOL:
            raise PermanentPortError(
                (
                    f"tool pack {manifest.id} credential {credential.name!r} has scope "
                    f"{credential.scope.value if credential.scope else 'NONE'}; "
                    "required tool credentials must be TOOL-scoped"
                ),
                failure_category=FailureCategory.VALIDATION_FAILURE,
            )


SubmitStatus = Literal["installed", "updated", "pending_approval", "unchanged", "revoked"]


@dataclass(frozen=True, slots=True)
class SubmitOutcome:
    """install/update 请求的结果：状态 + 记录 +（扩张时的）权限 diff。

    `unchanged` = 提交的 manifest 与生效版本内容一致（digest 相同），
    控制面不改写任何东西——调用方不应把它当成"更新成功"。
    """

    status: SubmitStatus
    record: ToolPackRecord
    diff: PermissionDiff | None = None


class ToolPackLifecycle:
    """ToolPack install/update/approve/revoke use case（副作用集中在 Port 边界）。"""

    def __init__(
        self,
        store: ToolPackStore,
        policy: PolicyEvaluator,
        events: EventPublisher,
        actor: str = "admin",
    ) -> None:
        self._store = store
        self._policy = policy
        self._events = events
        self._actor = actor

    def submit(self, manifest: ToolPackManifest) -> SubmitOutcome:
        """安装或提交更新：新 pack 直接安装；同 id 无扩张直接替换；扩张转待批准。"""
        _verify_supply_chain(manifest)
        existing = self._store.get(manifest.id)
        if existing is not None and existing.state is ToolPackState.REVOKED:
            raise InvalidInputError(f"revoked tool pack is terminal: {manifest.id}")
        if existing is None:
            return self._install_new(manifest)
        _require_decision(self._policy, self._actor, _UPDATE_CAPABILITY, manifest.id)
        if existing.manifest.digest == manifest.digest:
            return SubmitOutcome(status="unchanged", record=existing)
        diff = permission_diff(existing.manifest, manifest)
        if not diff.is_empty:
            return self._register_pending(existing, manifest, diff)
        return self._apply_update(existing, manifest)

    def _install_new(self, manifest: ToolPackManifest) -> SubmitOutcome:
        _require_decision(self._policy, self._actor, _INSTALL_CAPABILITY, manifest.id)
        record = ToolPackRecord(
            pack_id=manifest.id,
            state=ToolPackState.INSTALLED,
            manifest=manifest,
            installed_at=Timestamp.now(),
        )
        self._store.install(record)
        _publish(self._events, EventType.TOOL_PACK_INSTALLED, manifest.id, self._actor)
        return SubmitOutcome(status="installed", record=record)

    def _register_pending(
        self,
        existing: ToolPackRecord,
        manifest: ToolPackManifest,
        diff: PermissionDiff,
    ) -> SubmitOutcome:
        """扩张更新只登记待批准：生效版本与生效 digest 都保持不变。"""
        pending = ToolPackRecord(
            pack_id=existing.pack_id,
            state=existing.state,
            manifest=existing.manifest,
            installed_at=existing.installed_at,
            pending_manifest=manifest,
        )
        self._store.replace(pending)
        _publish(
            self._events,
            EventType.TOOL_PACK_UPDATED,
            manifest.id,
            self._actor,
            {"pending_approval": True},
        )
        return SubmitOutcome(status="pending_approval", record=pending, diff=diff)

    def _apply_update(self, existing: ToolPackRecord, manifest: ToolPackManifest) -> SubmitOutcome:
        record = ToolPackRecord(
            pack_id=manifest.id,
            state=ToolPackState.INSTALLED,
            manifest=manifest,
            installed_at=Timestamp.now(),
        )
        self._store.replace(record)
        _publish(
            self._events,
            EventType.TOOL_PACK_UPDATED,
            manifest.id,
            self._actor,
            {"expanded": False},
        )
        return SubmitOutcome(status="updated", record=record)

    def approve_update(self, pack_id: str) -> ToolPackRecord:
        """批准待批准的更新：此刻扩张才生效。无待批准 → InvalidInputError。"""
        existing = self._store.get(pack_id)
        if existing is None:
            raise InvalidInputError(f"tool pack not installed: {pack_id}")
        if existing.state is ToolPackState.REVOKED:
            raise InvalidInputError(f"revoked tool pack cannot be updated: {pack_id}")
        pending = existing.pending_manifest
        if pending is None:
            raise InvalidInputError(f"tool pack has no pending update: {pack_id}")
        _require_decision(
            self._policy,
            self._actor,
            f"{_UPDATE_CAPABILITY}.expanded",
            pack_id,
        )
        record = ToolPackRecord(
            pack_id=pack_id,
            state=ToolPackState.INSTALLED,
            manifest=pending,
            installed_at=Timestamp.now(),
        )
        self._store.replace(record)
        _publish(
            self._events,
            EventType.TOOL_PACK_UPDATED,
            pack_id,
            self._actor,
            {"expanded": True, "approved": True},
        )
        return record

    def revoke(self, pack_id: str, reason: str) -> ToolPackRecord:
        if not reason:
            raise InvalidInputError("revoke reason must not be empty")
        _require_decision(self._policy, self._actor, _REVOKE_CAPABILITY, pack_id)
        existing = self._store.get(pack_id)
        if existing is None:
            raise InvalidInputError(f"tool pack not installed: {pack_id}")
        if existing.state is ToolPackState.REVOKED:
            raise InvalidInputError(f"tool pack already revoked: {pack_id}")
        self._store.revoke(pack_id, reason)
        record = self._store.get(pack_id)
        assert record is not None
        _publish(
            self._events,
            EventType.TOOL_PACK_REVOKED,
            pack_id,
            self._actor,
            {"reason": reason},
        )
        return record
