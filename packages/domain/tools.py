"""Tool / Capability / Skill 域实体定义。

来源：docs/architecture/TOOL_RUNTIME.md、docs/architecture/CAPABILITY_SECURITY.md、
docs/security/PLUGIN_TOOL_SUPPLY_CHAIN.md、schemas/tool-provider.schema.json、
schemas/toolpack-manifest.schema.json。
AgentSession 启动后 Tool Set 冻结；ToolPack 需 immutable revision + digest + license。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from packages.domain.core import Digest, Timestamp, Version
from packages.domain.enums import (
    CredentialScope,
    EffectClass,
    EndpointHealth,
    FailureCategory,
    ProviderType,
    RiskClass,
    SkillStatus,
    ToolCallStatus,
    ToolResultStatus,
    TrustLevel,
)
from packages.domain.serialization import digest_of


@dataclass(frozen=True, slots=True)
class Capability:
    """稳定授权/语义单元（如 workspace.read、package.install）。"""

    id: str
    description: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("capability id must not be empty")


def _skill_content_dict(spec: SkillSpec) -> dict[str, object]:
    return {
        "id": spec.id,
        "version": spec.version.text,
        "capabilities": sorted(spec.capabilities),
        "description": spec.description,
    }


@dataclass(frozen=True, slots=True)
class SkillSpec:
    id: str
    version: Version
    capabilities: list[str] = field(default_factory=list)
    description: str = ""
    status: SkillStatus = SkillStatus.ACTIVE
    digest: Digest | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("skill id must not be empty")


def skill_content_digest(spec: SkillSpec) -> Digest:
    """Skill 内容确定性 digest（不含 digest 字段本身）。"""
    return digest_of(_skill_content_dict(spec))


@dataclass(frozen=True, slots=True)
class ToolSpec:
    id: str
    name: str
    effect_class: EffectClass
    provider_kind: ProviderType
    capabilities: list[str] = field(default_factory=list)
    description: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("tool id must not be empty")
        if not self.name:
            raise ValueError("tool name must not be empty")


def _tool_content_dict(tool: ToolSpec) -> dict[str, object]:
    return {
        "id": tool.id,
        "name": tool.name,
        "effect_class": tool.effect_class.value,
        "provider_kind": tool.provider_kind.value,
        "capabilities": sorted(tool.capabilities),
        "description": tool.description,
    }


@dataclass(frozen=True, slots=True)
class ToolProviderSpec:
    id: str
    kind: ProviderType
    trust_level: TrustLevel
    capabilities: list[str] = field(default_factory=list)
    effect_class: EffectClass = EffectClass.READ_ONLY
    transport: str | None = None
    endpoint_env: str | None = None
    network_domains: list[str] = field(default_factory=list)
    protocol_version: str | None = None
    health_check: bool = False

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("tool provider id must not be empty")


@dataclass(frozen=True, slots=True)
class ToolHealthReport:
    """ToolProvider 健康探测结果（MCP_TOOL_PROVIDERS.md §6）。"""

    provider_id: str
    status: EndpointHealth
    observed_schema_digest: Digest | None = None
    detail: str = ""

    def __post_init__(self) -> None:
        if not self.provider_id:
            raise ValueError("provider_id must not be empty")


def classify_risk(effect_class: EffectClass, trust_level: TrustLevel) -> RiskClass:
    """effect/risk 分层：EffectClass 描述副作用类别，TrustLevel 描述来源可信度。

    高风险组合优先；UNTRUSTED/REVOKED 一律 CRITICAL。
    """
    if trust_level in (TrustLevel.UNTRUSTED, TrustLevel.REVOKED):
        return RiskClass.CRITICAL
    if effect_class in (EffectClass.DESTRUCTIVE, EffectClass.EXTERNAL_PUBLISH):
        return RiskClass.CRITICAL
    if effect_class in (EffectClass.SECRET_USE, EffectClass.EXECUTE):
        return RiskClass.HIGH
    if effect_class in (EffectClass.WRITE, EffectClass.NETWORK):
        return RiskClass.MEDIUM
    if trust_level is TrustLevel.USER_APPROVED:
        return RiskClass.MEDIUM
    return RiskClass.LOW


@dataclass(frozen=True, slots=True)
class CredentialRequirement:
    name: str
    scope: CredentialScope | None = None
    required: bool = True


def _manifest_content_dict(manifest: ToolPackManifest) -> dict[str, object]:
    return {
        "id": manifest.id,
        "version": manifest.version.text,
        "source": manifest.source,
        "resolved_revision": manifest.resolved_revision,
        "license": manifest.license,
        "tools": [_tool_content_dict(tool) for tool in manifest.tools],
        "skills": [_skill_content_dict(skill) for skill in manifest.skills],
        "requested_capabilities": sorted(manifest.requested_capabilities),
        "network_domains": sorted(manifest.network_domains),
        "credentials": [
            {
                "name": credential.name,
                "scope": credential.scope.value if credential.scope else None,
                "required": credential.required,
            }
            for credential in manifest.credentials
        ],
    }


def toolpack_content_digest(manifest: ToolPackManifest) -> Digest:
    """ToolPack 内容确定性 digest（不含 digest/signature 字段本身）。"""
    return digest_of(_manifest_content_dict(manifest))


@dataclass(frozen=True, slots=True)
class ToolPackManifest:
    id: str
    version: Version
    source: str
    resolved_revision: str
    digest: Digest
    license: str
    tools: list[ToolSpec] = field(default_factory=list)
    skills: list[SkillSpec] = field(default_factory=list)
    requested_capabilities: list[str] = field(default_factory=list)
    network_domains: list[str] = field(default_factory=list)
    credentials: list[CredentialRequirement] = field(default_factory=list)
    signature: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("tool pack id must not be empty")
        if not self.source:
            raise ValueError("tool pack source must not be empty")
        if not self.resolved_revision:
            raise ValueError("tool pack resolved_revision must not be empty")
        if not self.license:
            raise ValueError("tool pack license must not be empty")

    def verify_content_digest(self) -> bool:
        """manifest.digest 与内容重算一致（digest 篡改检测）。"""
        return self.digest == toolpack_content_digest(self)


@dataclass(frozen=True, slots=True)
class ToolCallRecord:
    task_id: str
    attempt: int
    operation_key: str
    tool_id: str
    capability: str
    argument_digest: Digest
    status: ToolCallStatus = ToolCallStatus.REQUESTED
    recorded_at: object | None = None

    def __post_init__(self) -> None:
        if not self.tool_id:
            raise ValueError("tool id must not be empty")


@dataclass(frozen=True, slots=True)
class ToolResultRecord:
    """工具执行结果（M5 ToolProvider 输出）。

    output 只保存 digest，内容经 ArtifactStore 持久化；
    错误消息必须已 redaction（secret 永不进入记录）。
    """

    task_id: str
    attempt: int
    operation_key: str
    tool_id: str
    status: ToolResultStatus
    output_digest: Digest | None = None
    failure_category: FailureCategory | None = None
    error_message_redacted: str | None = None
    recorded_at: Timestamp | None = None

    def __post_init__(self) -> None:
        if not self.task_id:
            raise ValueError("task_id must not be empty")
        if not self.operation_key:
            raise ValueError("operation_key must not be empty")
        if not self.tool_id:
            raise ValueError("tool_id must not be empty")
        if self.failure_category is not None and self.error_message_redacted is None:
            raise ValueError("failed tool result must carry redacted error message")


@dataclass(frozen=True, slots=True)
class CapabilityGrant:
    agent_id: str
    capability: str
    scope: str = "session"
    revocable: bool = True
