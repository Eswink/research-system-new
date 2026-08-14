"""ToolPack lifecycle use case：install / update / revoke（ADR-0019）。

供应链验证（digest 校验）在安装门禁内：manifest.digest 必须与内容
重算一致；update 需权限 diff（requested_capabilities / network_domains
/ credentials 差集）并通过 policy 审批；revoke 记录原因并发布领域事件。
"""

from __future__ import annotations

from dataclasses import dataclass

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


class ToolPackLifecycle:
    """ToolPack install/update/revoke use case（副作用集中在 Port 边界）。"""

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

    def install(self, manifest: ToolPackManifest) -> ToolPackRecord:
        _verify_supply_chain(manifest)
        _require_decision(self._policy, self._actor, _INSTALL_CAPABILITY, manifest.id)
        if self._store.get(manifest.id) is not None:
            raise InvalidInputError(f"tool pack already installed: {manifest.id}")
        record = ToolPackRecord(
            pack_id=manifest.id,
            state=ToolPackState.INSTALLED,
            manifest=manifest,
            installed_at=Timestamp.now(),
        )
        self._store.install(record)
        _publish(self._events, EventType.TOOL_PACK_INSTALLED, manifest.id, self._actor)
        return record

    def update(self, manifest: ToolPackManifest) -> ToolPackRecord:
        _verify_supply_chain(manifest)
        _require_decision(self._policy, self._actor, _UPDATE_CAPABILITY, manifest.id)
        existing = self._store.get(manifest.id)
        if existing is None:
            raise InvalidInputError(f"tool pack not installed: {manifest.id}")
        if existing.state is ToolPackState.REVOKED:
            raise InvalidInputError(f"revoked tool pack cannot be updated: {manifest.id}")
        diff = permission_diff(existing.manifest, manifest)
        if not diff.is_empty:
            _require_decision(
                self._policy,
                self._actor,
                f"{_UPDATE_CAPABILITY}.expanded",
                manifest.id,
            )
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
            {"expanded": not diff.is_empty},
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
