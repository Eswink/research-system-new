"""RunManifest 不可变语义快照 + Revision。

来源：docs/architecture/DOMAIN_MODEL.md（RunManifest / RunManifestRevision）、
docs/architecture/DETERMINISTIC_SERIALIZATION.md（canonical digest 规则）。
Manifest 一旦冻结不可原地修改；改变关键依赖必须 fork run 或显式
revision + approval + audit（AGENTS.md §5）。

M7 边界（诚实声明）：以下字段当前无法从 compile/preflight 上下文获取，
保持 None/空（不做伪填充）：source_commit（无 git 元数据来源）、
model_runtime_fingerprints（真实 model probe 在 M8 接入）、
context_template_hashes（Context Engine 未落地）、execution_backend /
environment（runtime 装配由 OpenHandsRuntimeAdapter 决定，adapter 不反向
上报执行环境标识）、input_artifact_digests（M7 场景无输入 Artifact）。
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field

from packages.domain.core import Digest, Timestamp, Version
from packages.domain.serialization import digest_of


@dataclass(frozen=True, slots=True)
class RunManifest:
    """不可变语义快照：digest 覆盖全部声明字段。

    M12-R1 扩展（兼容新增 optional 字段，digest 自动覆盖）：
    - model_runtime_fingerprints：真实 probe 结果或 NOT_VERIFIED 占位（AGENTS.md §4）；
    - endpoint_config_digest / probe_suite_digest：relay 配置与 probe suite 的
      canonical digest（不含 credential 明文）；
    - fallback_audit：显式冻结 fallback 语义；无 fallback 时必须为
      {"mode": "none"}，有则记录 requested → selected + trigger；
    - image_digest：实验沙箱镜像 digest（M9 真实容器执行）；
    - skill_versions：M8 Skill Registry 版本/digest pin；
    - evaluation_dataset_digest：M11 评测数据集冻结 digest。
    """

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
    task_contracts: dict[str, object] = field(default_factory=dict)
    policy_version: str | None = None
    context_template_hashes: list[str] = field(default_factory=list)
    workspace_backend: str | None = None
    execution_backend: str | None = None
    environment: str | None = None
    input_artifact_digests: list[str] = field(default_factory=list)
    budget_reservation_ref: str | None = None
    frozen_at: Timestamp | None = None
    # --- M12-R1 扩展字段（全部 optional；None/空 = 未冻结，不伪填充） ---
    endpoint_config_digest: str | None = None
    probe_suite_digest: str | None = None
    fallback_audit: dict[str, object] = field(default_factory=dict)
    image_digest: str | None = None
    skill_versions: dict[str, str] = field(default_factory=dict)
    evaluation_dataset_digest: str | None = None

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("manifest run_id must not be empty")
        if not self.project_id:
            raise ValueError("manifest project_id must not be empty")

    def digest(self) -> Digest:
        """Manifest 的 sha256 确定性 digest。"""
        return digest_of(self)

    def semantic_digest(self) -> Digest:
        """语义 digest：覆盖除 frozen_at 外的全部声明字段。

        frozen_at 是冻结时刻的元数据，不参与语义比对；其余任何字段漂移
        （模型、工具、角色、契约、预算预留、策略版本）都会改变本 digest。
        用于 resume/fork 的一致性校验（AGENTS.md §5、WORKFLOW_RELIABILITY.md §8）。
        """
        payload = dataclasses.asdict(self)
        payload.pop("frozen_at", None)
        return digest_of(payload)


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
        # changes 结构不变量（M7 技术债清偿）：空修订与非 str key 拒绝，
        # 防止绕过 manifest 语义的任意内容写入。
        if not self.changes:
            raise ValueError("revision changes must not be empty")
        if not all(isinstance(key, str) for key in self.changes):
            raise ValueError("revision changes keys must be strings")
