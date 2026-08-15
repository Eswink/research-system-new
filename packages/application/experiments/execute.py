"""Experiment 执行 use case（M9 Real Experiment Runtime）。

打通 `ExperimentPlan → ExperimentRun → Metric → Artifact`：
1. 经 WorkspaceBackend 获取 WorkspaceLease（无 Lease 不执行）+ pre-snapshot；
2. 构造 ExecutionSpec（workspace_path/env/environment_digest）经
   ExecutionBackend 执行（容器边界由 backend 施加）；
3. stdout/stderr/experiment_result.json/引用文件作为内容寻址 Artifact
   写入 ArtifactStore（artifact_ingest.py；内容持久化不拥有 Evidence
   truth）；
4. 解析 experiment_result.json → 类型化 MetricValue；
5. 状态分类（NEGATIVE_RESULT 语义，见 classification.py）；
6. post-snapshot，构造 ExperimentRun 终态结果。

执行输出契约（backend 侧）：DockerExecutionBackend 在每次执行后把
stdout/stderr 全文写入挂载工作区根目录的 stdout.log / stderr.log；
实验命令在工作区写 experiment_result.json。这些文件进入 post-snapshot，
构成可复现性绑定（WORKSPACE_RUNTIME.md §8）。

本用例不重写 run_orchestration 的 Agent 会话路径；与编排链的集成点
（task 类型映射）留给 M12。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from packages.application.experiments.artifact_ingest import (
    read_result_payload,
    store_file_artifact,
    store_log_artifact,
    store_referenced_artifacts,
)
from packages.application.experiments.classification import (
    classify_outcome,
    execution_failure_reason,
    image_digest_from_run,
)
from packages.application.experiments.types import (
    MEDIA_JSON,
    RESULT_FILE,
    STDERR_LOG,
    STDOUT_LOG,
    ExperimentExecutionOutcome,
    ExperimentExecutionRequest,
    WorkspaceDirResolver,
)
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.execution_backend import ExecutionBackend
from packages.application.ports.workspace_backend import WorkspaceBackend
from packages.domain.core import Digest
from packages.domain.experiment_state import ExperimentRunState
from packages.domain.experiments import (
    ExperimentRun,
    ExperimentRunResult,
    ExperimentRunSpec,
    MetricValue,
)
from packages.domain.serialization import digest_of
from packages.domain.workspace import (
    ExecutionRun,
    ExecutionSpec,
    ExecutionStatus,
    WorkspaceLease,
    WorkspaceSnapshot,
)


@dataclass(frozen=True, slots=True)
class _Collected:
    """容器执行后的产出聚合（execute 步骤间传递）。"""

    stdout_id: str | None
    stderr_id: str | None
    result_artifact_id: str | None
    metric_values: tuple[MetricValue, ...]
    metrics_digest: Digest | None
    referenced_ids: tuple[str, ...]
    transition_event: str
    failure_reason: str | None


class ExperimentExecutor:
    """实验执行编排；依赖全部来自 Port（application 拥有 Port）。"""

    def __init__(
        self,
        *,
        execution: ExecutionBackend,
        workspaces: WorkspaceBackend,
        artifacts: ArtifactStore,
        workspace_dir: WorkspaceDirResolver,
    ) -> None:
        self._execution = execution
        self._workspaces = workspaces
        self._artifacts = artifacts
        self._workspace_dir = workspace_dir

    def execute(self, request: ExperimentExecutionRequest) -> ExperimentExecutionOutcome:
        run = self._start_run(request)
        execution_run, lease, snapshot_before, workspace_path = self._run_container(request, run)
        collected = self._collect_outputs(request, workspace_path, execution_run)
        return self._finalize(run, execution_run, lease, snapshot_before, collected)

    def _start_run(self, request: ExperimentExecutionRequest) -> ExperimentRun:
        spec = self._build_run_spec(request)
        run = ExperimentRun(id=request.run_id, plan_id=request.plan.id, spec=spec)
        return run.transition(ExperimentRunState.Transition.START)

    def _run_container(
        self, request: ExperimentExecutionRequest, run: ExperimentRun
    ) -> tuple[ExecutionRun, WorkspaceLease, WorkspaceSnapshot, Path]:
        assert run.spec is not None
        lease = self._workspaces.acquire_lease(request.workspace, request.agent_session_id)
        snapshot_before = self._workspaces.snapshot(lease)
        workspace_path = self._workspace_dir(lease)
        execution_run = self._execution.execute(
            self._build_execution_spec(request, run.spec, workspace_path),
            timeout_seconds=request.timeout_seconds,
        )
        return execution_run, lease, snapshot_before, workspace_path

    def _collect_outputs(
        self,
        request: ExperimentExecutionRequest,
        workspace_path: Path,
        execution_run: ExecutionRun,
    ) -> _Collected:
        stdout_id = store_log_artifact(
            self._artifacts,
            request.run_id,
            workspace_path,
            STDOUT_LOG,
            execution_run.stdout_digest,
        )
        stderr_id = store_log_artifact(
            self._artifacts,
            request.run_id,
            workspace_path,
            STDERR_LOG,
            execution_run.stderr_digest,
        )
        result_artifact_id: str | None = None
        metric_values: tuple[MetricValue, ...] = ()
        metrics_digest: Digest | None = None
        referenced_ids: tuple[str, ...] = ()
        declared_status: str | None = None
        if execution_run.status is ExecutionStatus.SUCCEEDED:
            (
                result_artifact_id,
                metric_values,
                metrics_digest,
                referenced_ids,
                declared_status,
            ) = self._ingest_success_outputs(request, workspace_path)
        event, reason = classify_outcome(execution_run.status, declared_status)
        failure_reason = execution_failure_reason(execution_run.status)
        if reason is not None:
            failure_reason = failure_reason or reason
        return _Collected(
            stdout_id=stdout_id,
            stderr_id=stderr_id,
            result_artifact_id=result_artifact_id,
            metric_values=metric_values,
            metrics_digest=metrics_digest,
            referenced_ids=referenced_ids,
            transition_event=event,
            failure_reason=failure_reason,
        )

    def _ingest_success_outputs(
        self, request: ExperimentExecutionRequest, workspace_path: Path
    ) -> tuple[str | None, tuple[MetricValue, ...], Digest | None, tuple[str, ...], str | None]:
        payload = read_result_payload(workspace_path, request.run_id)
        if payload is None:
            return None, (), None, (), None
        referenced_ids = store_referenced_artifacts(
            self._artifacts, request.run_id, workspace_path, payload.artifact_refs
        )
        result_artifact_id = store_file_artifact(
            self._artifacts,
            request.run_id,
            workspace_path / RESULT_FILE,
            classification="experiment_result",
            media_type=MEDIA_JSON,
        )
        return (
            result_artifact_id,
            payload.metric_values,
            payload.metrics_digest,
            referenced_ids,
            payload.declared_status,
        )

    def _finalize(
        self,
        run: ExperimentRun,
        execution_run: ExecutionRun,
        lease: WorkspaceLease,
        snapshot_before: WorkspaceSnapshot,
        collected: _Collected,
    ) -> ExperimentExecutionOutcome:
        snapshot_after = self._workspaces.snapshot(lease)
        result = ExperimentRunResult(
            execution_run_id=execution_run.run_id,
            image_digest=image_digest_from_run(execution_run),
            workspace_snapshot_before=snapshot_before.digest,
            workspace_snapshot_after=snapshot_after.digest,
            stdout_digest=execution_run.stdout_digest,
            stderr_digest=execution_run.stderr_digest,
            metrics=collected.metric_values,
            metrics_digest=collected.metrics_digest,
            artifact_refs=tuple(
                artifact_id
                for artifact_id in (
                    collected.stdout_id,
                    collected.stderr_id,
                    collected.result_artifact_id,
                    *collected.referenced_ids,
                )
                if artifact_id is not None
            ),
            failure_reason=collected.failure_reason,
        )
        run = run.with_result(result).transition(collected.transition_event)
        return ExperimentExecutionOutcome(
            run=run,
            stdout_artifact_id=collected.stdout_id,
            stderr_artifact_id=collected.stderr_id,
            result_artifact_id=collected.result_artifact_id,
        )

    def _build_run_spec(self, request: ExperimentExecutionRequest) -> ExperimentRunSpec:
        input_payload = {
            "experiment_spec": request.command,
            "hypothesis": request.plan.hypothesis,
            "seed": request.seed,
        }
        environment_digest = digest_of(dict(request.environment)) if request.environment else None
        return ExperimentRunSpec(
            input_digest=digest_of(input_payload),
            code_digest=request.code_digest,
            environment_digest=environment_digest,
            seed=request.seed,
            resource_profile=request.resource_profile,
        )

    def _build_execution_spec(
        self,
        request: ExperimentExecutionRequest,
        run_spec: ExperimentRunSpec,
        workspace_path: Path,
    ) -> ExecutionSpec:
        return ExecutionSpec(
            backend_kind="sandbox",
            command=request.command,
            resource_profile=request.resource_profile,
            environment_digest=(
                str(run_spec.environment_digest) if run_spec.environment_digest else None
            ),
            workspace_path=str(workspace_path),
            environment=dict(request.environment),
        )
