"""ReproducibilityAudit use case（M9）。

从终态 ExperimentRun + ArtifactStore 构建 ReproducibilityAudit：
- 输入/代码/环境/seed/资源/镜像 pin/前后 snapshot/输出 artifact digests/
  metrics digest 全部绑定；
- audit_digest 由确定性 canonical payload 计算（digest_of）；
- 复核（verify）可在后续任何时间检测绑定漂移/篡改。

非职责：audit 记录本身不进 ArtifactStore（Canonical State 归属与
ExperimentRun 一致，M14 PostgreSQL 持久化）；这里只产出领域对象。
"""

from __future__ import annotations

from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import ID, Digest
from packages.domain.experiment_state import ExperimentRunState
from packages.domain.experiments import ExperimentRun, ExperimentRunResult
from packages.domain.reproducibility import ReproducibilityAudit
from packages.domain.serialization import digest_of


def build_reproducibility_audit(
    run: ExperimentRun,
    *,
    audit_id: ID,
    artifacts: ArtifactStore,
) -> ReproducibilityAudit:
    """从终态 ExperimentRun 构建并封存（audit_digest）复现性审计。"""
    if not run.is_terminal:
        raise InvalidInputError(
            f"cannot audit non-terminal experiment run {run.id.value} (state={run.state})"
        )
    spec = run.spec
    result = run.result
    if spec is None or result is None:
        raise InvalidInputError("terminal experiment run must carry spec and result")
    digest_by_id = {artifact.id: artifact.digest for artifact in artifacts.list_refs()}
    return ReproducibilityAudit(
        audit_id=audit_id,
        experiment_run_id=run.id,
        input_digest=spec.input_digest,
        code_digest=spec.code_digest,
        environment_digest=spec.environment_digest,
        seed=spec.seed,
        resource_profile=spec.resource_profile,
        image_digest=result.image_digest,
        workspace_snapshot_before=result.workspace_snapshot_before,
        workspace_snapshot_after=result.workspace_snapshot_after,
        output_artifact_digests=_resolve_output_digests(result, digest_by_id),
        metrics_digest=_metrics_digest(result),
    ).with_audit_digest()


def verify_reproducibility_audit(audit: ReproducibilityAudit) -> bool:
    """复核 audit_digest 与当前绑定载荷一致（漂移检测）。"""
    return audit.verify()


def is_auditable_state(state: str) -> bool:
    """只有科学终态（成功/负结论）进入审计；执行失败/超时/取消不审计。"""
    return state in (
        ExperimentRunState.State.SUCCEEDED,
        ExperimentRunState.State.NEGATIVE_RESULT,
    )


def _resolve_output_digests(
    result: ExperimentRunResult, digest_by_id: dict[str, Digest]
) -> tuple[str, ...]:
    digests: list[str] = []
    for artifact_id in result.artifact_refs:
        digest = digest_by_id.get(artifact_id)
        if digest is None:
            raise InvalidInputError(f"artifact ref {artifact_id!r} not found in artifact store")
        digests.append(str(digest))
    return tuple(digests)


def _metrics_digest(result: ExperimentRunResult) -> Digest | None:
    """优先采用执行时从 experiment_result.json 解析的 metrics digest。"""
    if result.metrics_digest is not None:
        return result.metrics_digest
    if not result.metrics:
        return None
    return digest_of(result.metrics)
