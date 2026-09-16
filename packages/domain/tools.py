"""Tool / Capability / Skill 域实体定义。

来源：docs/architecture/TOOL_RUNTIME.md、docs/architecture/CAPABILITY_SECURITY.md、
docs/security/PLUGIN_TOOL_SUPPLY_CHAIN.md、schemas/tool-provider.schema.json、
schemas/toolpack-manifest.schema.json。
AgentSession 启动后 Tool Set 冻结；ToolPack 需 immutable revision + digest + license。
"""

from __future__ import annotations

from collections.abc import Mapping
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


def manifest_document(manifest: ToolPackManifest) -> dict[str, object]:
    """manifest 的可序列化文档（内容 + digest + signature）。

    内容部分复用 `_manifest_content_dict`（digest 的计算口径），因此
    「文档 → manifest → 重算内容 digest」的往返不会因新增字段而漂移：
    文档里多出来的只有 digest/signature 本身，而它们不参与内容 digest。
    """
    document = _manifest_content_dict(manifest)
    document["digest"] = str(manifest.digest)
    document["signature"] = manifest.signature
    return document


def _required_str(raw: Mapping[str, object], key: str, where: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{where}.{key} must be a non-empty string")
    return value


def _str_list(raw: Mapping[str, object], key: str, where: str) -> list[str]:
    value = raw.get(key)
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{where}.{key} must be a list of strings")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise ValueError(f"{where}.{key} must contain non-empty strings")
        items.append(item)
    return items


def _object_list(raw: Mapping[str, object], key: str, where: str) -> list[Mapping[str, object]]:
    value = raw.get(key)
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{where}.{key} must be a list of objects")
    items: list[Mapping[str, object]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError(f"{where}.{key} must contain objects")
        items.append(item)
    return items


def _tools_from_document(document: Mapping[str, object]) -> list[ToolSpec]:
    return [
        ToolSpec(
            id=_required_str(item, "id", "tools[]"),
            name=_required_str(item, "name", "tools[]"),
            effect_class=EffectClass(_required_str(item, "effect_class", "tools[]")),
            provider_kind=ProviderType(_required_str(item, "provider_kind", "tools[]")),
            capabilities=_str_list(item, "capabilities", "tools[]"),
            description=str(item.get("description") or ""),
        )
        for item in _object_list(document, "tools", "manifest")
    ]


def _skills_from_document(document: Mapping[str, object]) -> list[SkillSpec]:
    return [
        SkillSpec(
            id=_required_str(item, "id", "skills[]"),
            version=Version(_required_str(item, "version", "skills[]")),
            capabilities=_str_list(item, "capabilities", "skills[]"),
            description=str(item.get("description") or ""),
            status=SkillStatus(str(item["status"])) if item.get("status") else SkillStatus.ACTIVE,
            digest=Digest.parse(str(item["digest"])) if item.get("digest") else None,
        )
        for item in _object_list(document, "skills", "manifest")
    ]


def _credentials_from_document(document: Mapping[str, object]) -> list[CredentialRequirement]:
    return [
        CredentialRequirement(
            name=_required_str(item, "name", "credentials[]"),
            scope=CredentialScope(str(item["scope"])) if item.get("scope") else None,
            required=bool(item.get("required", True)),
        )
        for item in _object_list(document, "credentials", "manifest")
    ]


def manifest_from_document(document: Mapping[str, object]) -> ToolPackManifest:
    """把文档还原成 ToolPackManifest；形状或枚举非法一律 ValueError（由调用方映射为 422）。

    与 `manifest_document` 构成往返：`manifest_from_document(manifest_document(m)) == m`
    （域对象为 frozen dataclass，可逐字段比较）。
    """
    raw_signature = document.get("signature")
    signature = raw_signature if isinstance(raw_signature, str) else None
    return ToolPackManifest(
        id=_required_str(document, "id", "manifest"),
        version=Version(_required_str(document, "version", "manifest")),
        source=_required_str(document, "source", "manifest"),
        resolved_revision=_required_str(document, "resolved_revision", "manifest"),
        digest=Digest.parse(_required_str(document, "digest", "manifest")),
        license=_required_str(document, "license", "manifest"),
        tools=_tools_from_document(document),
        skills=_skills_from_document(document),
        requested_capabilities=_str_list(document, "requested_capabilities", "manifest"),
        network_domains=_str_list(document, "network_domains", "manifest"),
        credentials=_credentials_from_document(document),
        signature=signature,
    )


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
