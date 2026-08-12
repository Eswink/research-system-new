"""Tool / Capability / Skill 域实体定义。

来源：docs/architecture/TOOL_RUNTIME.md、docs/architecture/CAPABILITY_SECURITY.md、
docs/security/PLUGIN_TOOL_SUPPLY_CHAIN.md、schemas/tool-provider.schema.json、
schemas/toolpack-manifest.schema.json。
AgentSession 启动后 Tool Set 冻结；ToolPack 需 immutable revision + digest + license。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from packages.domain.core import Digest, Version
from packages.domain.enums import EffectClass, ProviderType, TrustLevel


@dataclass(frozen=True, slots=True)
class Capability:
    """稳定授权/语义单元（如 workspace.read、package.install）。"""

    id: str
    description: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("capability id must not be empty")


@dataclass(frozen=True, slots=True)
class SkillSpec:
    id: str
    version: Version
    capabilities: list[str] = field(default_factory=list)
    description: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("skill id must not be empty")


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
class CredentialRequirement:
    name: str
    scope: str | None = None
    required: bool = True


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


@dataclass(frozen=True, slots=True)
class ToolCallRecord:
    task_id: str
    attempt: int
    operation_key: str
    tool_id: str
    capability: str
    argument_digest: Digest
    status: str
    recorded_at: object | None = None

    def __post_init__(self) -> None:
        if not self.tool_id:
            raise ValueError("tool id must not be empty")


@dataclass(frozen=True, slots=True)
class CapabilityGrant:
    agent_id: str
    capability: str
    scope: str = "session"
    revocable: bool = True
