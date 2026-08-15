"""ReproducibilityAudit 域实体（M9 Real Experiment Runtime）。

把一次 ExperimentRun 的输入、代码、环境、seed、资源配置、镜像 pin、
workspace snapshot（前后）与输出 artifact/metrics 绑定为一个确定性
audit_digest（digest_of canonical JSON）。状态 PASS/FAIL：
- PASS：所有可复现性必需锚点（image pin、前 snapshot、输出 artifact、
  metrics digest）齐全；
- FAIL：任一必需锚点缺失（例如镜像 digest 无法解析）。

Canonical State 边界：audit 记录本身是领域对象，持久化落点与
ExperimentRun 相同（M14 PostgreSQL），不放入 ArtifactStore。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from packages.domain.core import ID, Digest, Timestamp
from packages.domain.serialization import digest_of


@dataclass(frozen=True, slots=True)
class ReproducibilityAudit:
    """实验可复现性绑定记录；audit_digest 由 binding payload 确定性计算。"""

    audit_id: ID
    experiment_run_id: ID
    input_digest: Digest
    code_digest: Digest | None = None
    environment_digest: Digest | None = None
    seed: int | None = None
    resource_profile: str | None = None
    image_digest: str | None = None
    workspace_snapshot_before: str | None = None
    workspace_snapshot_after: str | None = None
    output_artifact_digests: tuple[str, ...] = ()
    metrics_digest: Digest | None = None
    audit_digest: Digest | None = None
    created_at: Timestamp = field(default_factory=Timestamp.now)

    def binding_payload(self) -> dict[str, Any]:
        """确定性绑定载荷（key 由 digest_of 排序；digest 统一 str 形式）。"""
        return {
            "experiment_run_id": str(self.experiment_run_id.value),
            "input_digest": str(self.input_digest),
            "code_digest": str(self.code_digest) if self.code_digest else None,
            "environment_digest": (
                str(self.environment_digest) if self.environment_digest else None
            ),
            "seed": self.seed,
            "resource_profile": self.resource_profile,
            "image_digest": self.image_digest,
            "workspace_snapshot_before": self.workspace_snapshot_before,
            "workspace_snapshot_after": self.workspace_snapshot_after,
            "output_artifact_digests": list(self.output_artifact_digests),
            "metrics_digest": str(self.metrics_digest) if self.metrics_digest else None,
        }

    def compute_audit_digest(self) -> Digest:
        return digest_of(self.binding_payload())

    def with_audit_digest(self) -> ReproducibilityAudit:
        return ReproducibilityAudit(
            audit_id=self.audit_id,
            experiment_run_id=self.experiment_run_id,
            input_digest=self.input_digest,
            code_digest=self.code_digest,
            environment_digest=self.environment_digest,
            seed=self.seed,
            resource_profile=self.resource_profile,
            image_digest=self.image_digest,
            workspace_snapshot_before=self.workspace_snapshot_before,
            workspace_snapshot_after=self.workspace_snapshot_after,
            output_artifact_digests=self.output_artifact_digests,
            metrics_digest=self.metrics_digest,
            audit_digest=self.compute_audit_digest(),
            created_at=self.created_at,
        )

    @property
    def status(self) -> str:
        required = (
            self.image_digest,
            self.workspace_snapshot_before,
            self.output_artifact_digests,
            self.metrics_digest,
        )
        return "PASS" if all(required) else "FAIL"

    def verify(self) -> bool:
        """audit_digest 与当前绑定载荷是否一致（篡改/漂移检测）。"""
        if self.audit_digest is None:
            return False
        return self.compute_audit_digest() == self.audit_digest
