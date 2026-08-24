"""ReproducibilityAudit 域实体（M9 Real Experiment Runtime）。

把一次 ExperimentRun 的 command/输入、代码、环境、seed、资源配置、
镜像 pin、workspace snapshot（前后）与输出 artifact/metrics 绑定为一个
确定性 audit_digest（digest_of canonical JSON）。状态 PASS/FAIL：
- PASS：所有可复现性必需锚点齐全且 audit 已封存；
- FAIL：任一必需锚点缺失（command/seed/environment/image/前后
  snapshot/输出 artifact/metrics digest 缺失，或 audit 未封存）。

findings() 返回结构化 AuditFinding（code/severity/message），使缺失
锚点可被程序化消费；code_digest 未单独 pin 时为 WARNING（代码已由
workspace_snapshot_before 覆盖）。

Canonical State 边界：audit 记录本身是领域对象，持久化落点与
ExperimentRun 相同（M14 PostgreSQL），不放入 ArtifactStore。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from packages.domain.core import ID, Digest, Timestamp
from packages.domain.serialization import digest_of


@dataclass(frozen=True, slots=True)
class AuditFinding:
    """一条结构化审计发现：稳定 code + 严重度 + 人类可读消息。"""

    code: str
    severity: str
    message: str

    @property
    def is_blocking(self) -> bool:
        return self.severity == "FAIL"


@dataclass(frozen=True, slots=True)
class ReproducibilityAudit:
    """实验可复现性绑定记录；audit_digest 由 binding payload 确定性计算。

    status 规则（FAIL 阻断，WARNING 不阻断）：
    - FAIL：command/seed/environment/image/前后 snapshot/输出 artifact/
      metrics digest 任一锚点缺失，或 audit 未封存；
    - WARNING：code_digest 未单独 pin。code_digest 语义 = 代码出处/内容的
      独立 provenance pin（由请求方可选提供，例如代码来自 repository
      commit 的场景）；工作区模型中代码内容已由 workspace_snapshot_before
      覆盖，故缺失时为 WARNING 而非 FAIL，诚实标注而非缺陷。
    """

    audit_id: ID
    experiment_run_id: ID
    input_digest: Digest
    command: str | None = None
    code_digest: Digest | None = None
    environment_digest: Digest | None = None
    seed: int | None = None
    resource_profile: str | None = None
    image_digest: str | None = None
    workspace_snapshot_before: str | None = None
    workspace_snapshot_after: str | None = None
    output_artifact_digests: tuple[str, ...] = ()
    metrics_digest: Digest | None = None
    semantic_metrics_digest: Digest | None = None
    observational_metrics_digest: Digest | None = None
    audit_digest: Digest | None = None
    created_at: Timestamp = field(default_factory=Timestamp.now)

    def binding_payload(self) -> dict[str, Any]:
        """确定性绑定载荷（key 由 digest_of 排序；digest 统一 str 形式）。

        M12-R1 WP4：metrics_digest 是复现锚点，覆盖科学指标投影
        （wall-clock 观测字段被剔除，跨重跑稳定）；observational_metrics_digest
        是审计附注（允许跨重跑漂移），不参与 audit digest——否则
        verify 会因观测 variance 误报漂移。
        旧 audit（semantic 为 None）回退到 raw metrics digest 语义。
        """
        return {
            "experiment_run_id": str(self.experiment_run_id.value),
            "input_digest": str(self.input_digest),
            "command": self.command,
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
            "semantic_metrics_digest": (
                str(self.semantic_metrics_digest) if self.semantic_metrics_digest else None
            ),
        }

    def compute_audit_digest(self) -> Digest:
        return digest_of(self.binding_payload())

    def with_audit_digest(self) -> ReproducibilityAudit:
        return ReproducibilityAudit(
            audit_id=self.audit_id,
            experiment_run_id=self.experiment_run_id,
            input_digest=self.input_digest,
            command=self.command,
            code_digest=self.code_digest,
            environment_digest=self.environment_digest,
            seed=self.seed,
            resource_profile=self.resource_profile,
            image_digest=self.image_digest,
            workspace_snapshot_before=self.workspace_snapshot_before,
            workspace_snapshot_after=self.workspace_snapshot_after,
            output_artifact_digests=self.output_artifact_digests,
            metrics_digest=self.metrics_digest,
            semantic_metrics_digest=self.semantic_metrics_digest,
            observational_metrics_digest=self.observational_metrics_digest,
            audit_digest=self.compute_audit_digest(),
            created_at=self.created_at,
        )

    def findings(self) -> tuple[AuditFinding, ...]:
        """对全部可复现性锚点执行真实检查，返回结构化发现。"""
        found = self._missing_anchor_findings()
        if self.code_digest is None:
            found.append(
                AuditFinding(
                    code="CODE_DIGEST_NOT_PINNED",
                    severity="WARNING",
                    message=(
                        "code provenance not separately pinned; code content is "
                        "covered by workspace_snapshot_before (WORKSPACE_RUNTIME.md §8)"
                    ),
                )
            )
        if self.semantic_metrics_digest is None:
            found.append(
                AuditFinding(
                    code="SEMANTIC_METRICS_DIGEST_MISSING",
                    severity="WARNING",
                    message=(
                        "semantic metrics digest not separated; metrics_digest may "
                        "include wall-clock observations (M12-R1 WP4)"
                    ),
                )
            )
        return tuple(found)

    def _missing_anchor_findings(self) -> list[AuditFinding]:
        """缺失锚点检查（FAIL 阻断项）。"""
        found: list[AuditFinding] = []

        def require(condition: bool, code: str, message: str) -> None:
            if not condition:
                found.append(AuditFinding(code=code, severity="FAIL", message=message))

        require(bool(self.command), "MISSING_COMMAND", "command (spec) not bound")
        require(self.seed is not None, "MISSING_SEED", "seed not pinned")
        require(
            self.environment_digest is not None,
            "MISSING_ENVIRONMENT_DIGEST",
            "environment digest not bound",
        )
        require(bool(self.image_digest), "MISSING_IMAGE_DIGEST", "image digest not pinned")
        require(
            bool(self.workspace_snapshot_before),
            "MISSING_CODE_SNAPSHOT",
            "workspace snapshot before (code snapshot) not bound",
        )
        require(
            bool(self.workspace_snapshot_after),
            "MISSING_SNAPSHOT_AFTER",
            "workspace snapshot after not bound",
        )
        require(
            bool(self.output_artifact_digests),
            "MISSING_OUTPUT_ARTIFACTS",
            "no output artifact digests bound",
        )
        require(
            self.metrics_digest is not None,
            "MISSING_METRICS_DIGEST",
            "metrics digest not bound",
        )
        require(self.audit_digest is not None, "UNSEALED_AUDIT", "audit digest not sealed")
        return found

    @property
    def status(self) -> str:
        return "FAIL" if any(f.is_blocking for f in self.findings()) else "PASS"

    def verify(self) -> bool:
        """audit_digest 与当前绑定载荷是否一致（篡改/漂移检测）。"""
        if self.audit_digest is None:
            return False
        return self.compute_audit_digest() == self.audit_digest
