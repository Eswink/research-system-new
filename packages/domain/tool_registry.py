"""Tool Provider 注册域（G15 / PLAN-20260915-060）。

供应链治理面（AGENTS.md §9「默认 deny：unpinned plugin」）在控制面的可写投影：
用户只能**注册/更新/批准/吊销**自己带来的 provider，不能让 provider 变成
`BUILT_IN`/`VERIFIED`——信任级别由**状态推导**，不由调用方声明：

    PENDING  → 未批准（不进入目录，preflight/决议看不到）
    ACTIVE   → USER_APPROVED（进入目录，成为可选来源）
    REVOKED  → REVOKED（终态，退出目录；再处置一律拒绝）

`pinned_revision` 必填：没有 pin 的注册就是"任意版本可漂移"，本仓明令禁止。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import Any

from packages.domain.core import Digest, Timestamp
from packages.domain.enums import EffectClass, EndpointHealth, ProviderType, TrustLevel
from packages.domain.state_base import InvalidTransitionError
from packages.domain.tools import ToolProviderSpec

MAX_PROVIDER_ID_LENGTH = 128
MAX_REVISION_LENGTH = 128
MAX_REASON_LENGTH = 1024
MAX_CAPABILITY_LENGTH = 128


class RegistrationState:
    """注册状态机（PENDING → ACTIVE → REVOKED，REVOKED 为终态）。"""

    class State(StrEnum):
        PENDING = "PENDING"
        ACTIVE = "ACTIVE"
        REVOKED = "REVOKED"

    class Transition(StrEnum):
        APPROVE = "APPROVE"
        REVOKE = "REVOKE"

    _TRANSITIONS: dict[str, dict[str, str]] = {
        State.PENDING: {Transition.APPROVE: State.ACTIVE, Transition.REVOKE: State.REVOKED},
        State.ACTIVE: {Transition.REVOKE: State.REVOKED},
        State.REVOKED: {},
    }

    @classmethod
    def initial(cls) -> str:
        return cls.State.PENDING.value

    @classmethod
    def terminal(cls) -> frozenset[str]:
        return frozenset({cls.State.REVOKED.value})

    @classmethod
    def transition(cls, current: str, event: str) -> str:
        allowed = cls._TRANSITIONS.get(current, {})
        if event not in allowed:
            raise InvalidTransitionError(current=current, event=event)
        return allowed[event]


def trust_for(state: str) -> TrustLevel:
    """信任级别由状态推导（不接受调用方声明）。"""
    if state == RegistrationState.State.ACTIVE.value:
        return TrustLevel.USER_APPROVED
    if state == RegistrationState.State.REVOKED.value:
        return TrustLevel.REVOKED
    return TrustLevel.UNTRUSTED


def _check_text(value: str, *, field: str, limit: int) -> None:
    if not value or len(value) > limit:
        raise ValueError(f"{field} must be non-empty and <= {limit} chars")


@dataclass(frozen=True, slots=True)
class ProviderRegistration:
    """一次 provider 注册（spec + pin + 生命周期 + 最近一次健康事实）。"""

    id: str
    kind: ProviderType
    capabilities: list[str]
    effect_class: EffectClass
    pinned_revision: str
    transport: str | None = None
    protocol_version: str | None = None
    network_domains: list[str] = field(default_factory=list)
    health_check: bool = False
    # 端点来源**声明**（环境变量名，值是端点 URL；PLAN-20260915-072）。这里只存
    # "变量名"：端点值永不入库、不进读面——解析发生在进程边界
    # （services/api/tool_provider_endpoints.py），凭据仍只走 CredentialResolver。
    endpoint_env: str | None = None
    # 凭据**必需性声明**（PLAN-20260915-074）：provider 声明"没有这个凭据我不可用"。
    # 与 endpoint_env 同样只存**名字**：值永不入库、不进读面——存在性判定走
    # CredentialResolver.has（services/api/tool_provider_credentials.py），
    # 取值只发生在进程边界。
    credential_ref: str | None = None
    state: str = RegistrationState.initial()
    registered_at: Timestamp | None = None
    updated_at: Timestamp | None = None
    approved_at: Timestamp | None = None
    revoked_at: Timestamp | None = None
    revoked_reason: str | None = None
    last_health: str | None = None
    health_detail: str | None = None
    health_checked_at: Timestamp | None = None
    schema_baseline_digest: str | None = None
    last_schema_digest: str | None = None
    schema_drift: bool = False
    schema_drift_since: Timestamp | None = None

    def __post_init__(self) -> None:
        _check_text(self.id, field="provider id", limit=MAX_PROVIDER_ID_LENGTH)
        # AGENTS.md §9「默认 deny：unpinned plugin」在这里成为硬门：pin 必须是
        # 内容寻址 digest（`sha256:<64hex>`），分支名/tag 这类可漂移字面量一律拒绝。
        if len(self.pinned_revision) > MAX_REVISION_LENGTH:
            raise ValueError(f"pinned revision must be <= {MAX_REVISION_LENGTH} chars")
        Digest.parse(self.pinned_revision)
        if not self.capabilities:
            raise ValueError("capabilities must not be empty")
        for capability in self.capabilities:
            _check_text(capability, field="capability", limit=MAX_CAPABILITY_LENGTH)
        if self.state == RegistrationState.State.REVOKED.value:
            if self.revoked_reason is None or not self.revoked_reason.strip():
                raise ValueError("revoked registration must carry a reason")
            if len(self.revoked_reason) > MAX_REASON_LENGTH:
                raise ValueError(f"revoked reason must be <= {MAX_REASON_LENGTH} chars")
        if self.transport is None and self.kind in {ProviderType.MCP, ProviderType.REST}:
            raise ValueError(f"{self.kind.value} provider must declare a transport")

    @property
    def active(self) -> bool:
        return self.state == RegistrationState.State.ACTIVE.value

    @property
    def trust_level(self) -> TrustLevel:
        return trust_for(self.state)

    def spec(self) -> ToolProviderSpec:
        """进入目录的 provider 规格（信任级别由状态推导，不取调用方输入）。"""
        return ToolProviderSpec(
            id=self.id,
            kind=self.kind,
            trust_level=self.trust_level,
            capabilities=sorted(set(self.capabilities)),
            effect_class=self.effect_class,
            transport=self.transport,
            protocol_version=self.protocol_version,
            network_domains=sorted(set(self.network_domains)),
            health_check=self.health_check,
            endpoint_env=self.endpoint_env,
            credential_ref=self.credential_ref,
        )

    def approve(self, *, now: Timestamp) -> ProviderRegistration:
        """批准（PENDING → ACTIVE）；同时**接受当前 schema 形态**作为新基线。

        批准是唯一显式的"我看见了并接受"动作，所以漂移在这里解除：基线换成最后一次
        观测到的 digest、漂移标志清除。若从未观测到 digest（没复核过），digest 字段不动。
        """
        state = RegistrationState.transition(self.state, RegistrationState.Transition.APPROVE)
        if self.last_schema_digest is None:
            return replace(self, state=state, approved_at=now, updated_at=now)
        return replace(
            self,
            state=state,
            approved_at=now,
            updated_at=now,
            schema_baseline_digest=self.last_schema_digest,
            schema_drift=False,
            schema_drift_since=None,
        )

    def revoke(self, reason: str, *, now: Timestamp) -> ProviderRegistration:
        stripped = reason.strip()
        if not stripped:
            raise ValueError("revocation reason must not be empty")
        if len(stripped) > MAX_REASON_LENGTH:
            raise ValueError(f"revocation reason must be <= {MAX_REASON_LENGTH} chars")
        state = RegistrationState.transition(self.state, RegistrationState.Transition.REVOKE)
        return replace(self, state=state, revoked_reason=stripped, revoked_at=now, updated_at=now)

    def record_health(
        self,
        status: EndpointHealth,
        *,
        detail: str,
        now: Timestamp,
        observed_schema_digest: str | None = None,
    ) -> ProviderRegistration:
        """记录一次健康探测事实（不改状态；REVOKED 仍可留痕）。

        `observed_schema_digest` 是提供方这次声明的 schema 指纹（能力面）。漂移是**状态**：

        - 首次观测 ⇒ 它成为基线（基线之前的漂移检测不到，注册面没有可比对象）；
        - 之后每次观测都拿**当前值 vs 基线**判定 `schema_drift`（不是 vs 上次）——
          否则 A→B→B 会让"变了"的告警在第二次复核后自己消失，而提供方仍不是当初那个；
        - **未观测到 digest（None）不动任何 digest 字段**：探测失败/无 digest 的 kind
          不等于"没变化"，把未知读成无漂移是最危险的误读。
        """
        if observed_schema_digest is None:
            return replace(
                self,
                last_health=status.value,
                health_detail=detail[:MAX_REASON_LENGTH],
                health_checked_at=now,
                updated_at=now,
            )
        Digest.parse(observed_schema_digest)
        baseline = self.schema_baseline_digest or observed_schema_digest
        drift = observed_schema_digest != baseline
        drift_since = self.schema_drift_since
        if drift and drift_since is None:
            drift_since = now
        if not drift:
            drift_since = None
        return replace(
            self,
            last_health=status.value,
            health_detail=detail[:MAX_REASON_LENGTH],
            health_checked_at=now,
            updated_at=now,
            schema_baseline_digest=baseline,
            last_schema_digest=observed_schema_digest,
            schema_drift=drift,
            schema_drift_since=drift_since,
        )

    def updated(self, changes: dict[str, Any], *, now: Timestamp) -> ProviderRegistration:
        """更新可变字段（id/state 不在其中；由状态机与路由共同约束）。"""
        if self.state == RegistrationState.State.REVOKED.value:
            raise InvalidTransitionError(current=self.state, event="UPDATE")
        merged = {**changes, "updated_at": now}
        return replace(self, **merged)
