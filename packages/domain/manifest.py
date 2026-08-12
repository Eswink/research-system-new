"""RunManifest 不可变语义快照 + Revision。

来源：docs/architecture/DOMAIN_MODEL.md（RunManifest / RunManifestRevision）、
docs/architecture/DETERMINISTIC_SERIALIZATION.md（canonical digest 规则）。
Manifest 一旦冻结不可原地修改；改变关键依赖必须 fork run 或显式
revision + approval + audit（AGENTS.md §5）。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from packages.domain.core import Digest, Timestamp, Version
from packages.domain.serialization import digest_of


@dataclass(frozen=True, slots=True)
class RunManifest:
    """不可变语义快照：digest 覆盖全部声明字段。"""

    run_id: str
    project_id: str
    protocol_version: Version
    protocol_digest: Digest | None = None
    compiled_plan_digest: Digest | None = None
    source_commit: str | None = None
    role_definitions: dict[str, object] = field(default_factory=dict)
    agent_specs: dict[str, object] = field(default_factory=dict)
    resolved_models: dict[str, str] = field(default_factory=dict)
    model_runtime_fingerprints: dict[str, object] = field(default_factory=dict)
    effective_tools: dict[str, object] = field(default_factory=dict)
    tool_pack_digests: list[str] = field(default_factory=list)
    policy_version: str | None = None
    context_template_hashes: list[str] = field(default_factory=list)
    workspace_backend: str | None = None
    execution_backend: str | None = None
    environment: str | None = None
    input_artifact_digests: list[str] = field(default_factory=list)
    budget_reservation_ref: str | None = None
    frozen_at: Timestamp | None = None

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("manifest run_id must not be empty")
        if not self.project_id:
            raise ValueError("manifest project_id must not be empty")

    def digest(self) -> Digest:
        """Manifest 的 sha256 确定性 digest。"""
        return digest_of(self)


@dataclass(frozen=True, slots=True)
class RunManifestRevision:
    """显式修订：必须带 approval 与 audit 记录，禁止原地修改 Manifest。"""

    manifest_digest: Digest
    base_digest: Digest
    revision_number: int
    reason: str
    changes: dict[str, object]
    approved_by: str
    approved_at: Timestamp
    audit_ref: str

    def __post_init__(self) -> None:
        if self.revision_number < 1:
            raise ValueError("revision_number must be >= 1")
        if not self.reason:
            raise ValueError("revision reason must not be empty")
        if not self.approved_by:
            raise ValueError("revision must record approver")
        if not self.audit_ref:
            raise ValueError("revision must carry an audit reference")
        if self.base_digest == self.manifest_digest:
            raise ValueError("revision must change the manifest digest")
