"""Experiment 全链容器 E2E（requires_docker）。

FileWorkspaceBackend + DockerExecutionBackend + SqliteArtifactStore：
- 确定性实验（固定 seed）在沙盒容器内真实执行；
- metrics 解析 + artifact 落库 + ExperimentRun 终态；
- NEGATIVE_RESULT（exit 0 + 声明负结论）≠ 执行失败；
- 同 input+seed+image → 同输出 digest（可复现性）；
- 变 seed → 输出 digest 变化；
- 容器 timeout → ExperimentRun TIMED_OUT。

实验代码文件（experiment.py）先写入租约工作区，命令为
`python experiment.py`（与真实实验形态一致）。
"""

from __future__ import annotations

import json
from pathlib import Path

import docker
import pytest
from docker.errors import ImageNotFound

from adapters.execution import DockerExecutionBackend
from adapters.sqlite.artifact_store import SqliteArtifactStore
from adapters.workspace import FileWorkspaceBackend
from packages.application.experiments import (
    ExperimentExecutionRequest,
    ExperimentExecutor,
    build_reproducibility_audit,
    verify_audit_outputs,
    verify_reproducibility_audit,
)
from packages.domain.core import ID
from packages.domain.experiment_state import ExperimentPlanState, ExperimentRunState
from packages.domain.experiments import ExperimentPlan
from packages.domain.workspace import Workspace

pytestmark = pytest.mark.requires_docker

IMAGE_TAG = "research-os-sandbox:m9-test"
_SANDBOX_DIR = Path(__file__).resolve().parents[3] / "adapters" / "execution" / "sandbox"

_PLAN_ID = ID("3f1c6a8e-9b2d-4f3a-8c5e-1a2b3c4d5e6f")
_WORKSPACE = Workspace(id="ws-exp", name="ws-exp")

# 确定性实验脚本：固定 seed 生成可复现输出（沙箱工作区内相对路径写入）
_EXPERIMENT_SCRIPT = """import json, random
from pathlib import Path
rng = random.Random(42)
samples = [rng.random() for _ in range(5)]
mean = sum(samples) / len(samples)
payload = {'experiment_run_id': 'RUN_ID', 'status': 'SUCCEEDED',
           'artifact_refs': ['samples.json'],
           'metrics': {'mean': mean, 'n_samples': len(samples)}}
Path('samples.json').write_text(json.dumps(samples), encoding='utf-8')
Path('experiment_result.json').write_text(json.dumps(payload), encoding='utf-8')
print('mean=', mean)
"""

_NEGATIVE_SCRIPT = """import json
from pathlib import Path
payload = {'experiment_run_id': 'RUN_ID', 'status': 'NEGATIVE_RESULT',
           'artifact_refs': [], 'metrics': {'effect_size': 0.03},
           'failure_ref': 'no significant effect'}
Path('experiment_result.json').write_text(json.dumps(payload), encoding='utf-8')
print('negative result recorded')
"""


@pytest.fixture(scope="module")
def image() -> str:
    client = docker.from_env()
    try:
        client.ping()
    except Exception:
        pytest.skip("docker daemon unavailable")
    try:
        client.images.get(IMAGE_TAG)
    except ImageNotFound:
        client.images.build(path=str(_SANDBOX_DIR), tag=IMAGE_TAG)
    return IMAGE_TAG


@pytest.fixture()
def harness(
    tmp_path: Path, image: str
) -> tuple[ExperimentExecutor, FileWorkspaceBackend, SqliteArtifactStore]:
    workspaces = FileWorkspaceBackend(tmp_path / "workspaces")
    workspaces.create_workspace(_WORKSPACE)
    artifacts = SqliteArtifactStore(blob_dir=tmp_path / "blobs")
    executor = ExperimentExecutor(
        execution=DockerExecutionBackend(image=image),
        workspaces=workspaces,
        artifacts=artifacts,
        workspace_dir=lambda lease: workspaces.workspace_dir(lease),
    )
    return executor, workspaces, artifacts


def _plan() -> ExperimentPlan:
    return ExperimentPlan(
        id=_PLAN_ID,
        name="seed-determinism",
        hypothesis="fixed seed produces fixed output",
    ).transition(ExperimentPlanState.Transition.PREREGISTER)


def _prepare(
    workspaces: FileWorkspaceBackend, run_id: ID, script: str, *, seed: int | None = 42
) -> ExperimentExecutionRequest:
    """把实验代码写入租约工作区，返回执行请求。"""
    session_id = f"session-{run_id.value[:8]}"
    lease = workspaces.acquire_lease(_WORKSPACE, session_id)
    workspace_dir = workspaces.workspace_dir(lease)
    (workspace_dir / "experiment.py").write_text(
        script.replace("RUN_ID", str(run_id.value)), encoding="utf-8"
    )
    return ExperimentExecutionRequest(
        plan=_plan(),
        run_id=run_id,
        command="python experiment.py",
        workspace=_WORKSPACE,
        agent_session_id=session_id,
        seed=seed,
        resource_profile="small",
        timeout_seconds=60,
    )


class TestExperimentE2E:
    def test_deterministic_experiment_full_chain(
        self, harness: tuple[ExperimentExecutor, FileWorkspaceBackend, SqliteArtifactStore]
    ) -> None:
        executor, workspaces, artifacts = harness
        run_id = ID("11111111-2222-4333-8444-555555555555")
        outcome = executor.execute(_prepare(workspaces, run_id, _EXPERIMENT_SCRIPT))
        assert outcome.run.state == ExperimentRunState.State.SUCCEEDED
        result = outcome.run.result
        assert result is not None
        assert result.image_digest is not None and result.image_digest.startswith("sha256:")
        assert result.workspace_snapshot_before is not None
        assert result.workspace_snapshot_after is not None
        assert result.workspace_snapshot_before != result.workspace_snapshot_after
        assert result.metrics[0].metric.name == "mean"
        assert result.metrics[1].metric.name == "n_samples"
        assert f"{run_id.value}:experiment_result.json" in result.artifact_refs
        assert f"{run_id.value}:samples.json" in result.artifact_refs
        assert f"{run_id.value}:stdout.log" in result.artifact_refs
        assert artifacts.verify(f"{run_id.value}:experiment_result.json")
        assert artifacts.verify(f"{run_id.value}:samples.json")
        stdout = artifacts.get(f"{run_id.value}:stdout.log")
        assert b"mean=" in stdout

    def test_same_input_same_output_digest(
        self, harness: tuple[ExperimentExecutor, FileWorkspaceBackend, SqliteArtifactStore]
    ) -> None:
        executor, workspaces, artifacts = harness
        first_id = ID("aaaaaaaa-2222-4333-8444-555555555555")
        second_id = ID("bbbbbbbb-2222-4333-8444-555555555555")
        first = executor.execute(_prepare(workspaces, first_id, _EXPERIMENT_SCRIPT))
        second = executor.execute(_prepare(workspaces, second_id, _EXPERIMENT_SCRIPT))
        assert first.run.result is not None and second.run.result is not None
        assert first.run.spec is not None and second.run.spec is not None
        assert first.run.spec.input_digest == second.run.spec.input_digest
        assert first.run.result.image_digest == second.run.result.image_digest
        first_output = artifacts.get(f"{first_id.value}:samples.json")
        second_output = artifacts.get(f"{second_id.value}:samples.json")
        assert first_output == second_output

    def test_different_seed_different_input_digest(
        self, harness: tuple[ExperimentExecutor, FileWorkspaceBackend, SqliteArtifactStore]
    ) -> None:
        executor, workspaces, _ = harness
        first_id = ID("cccccccc-2222-4333-8444-555555555555")
        second_id = ID("dddddddd-2222-4333-8444-555555555555")
        first = executor.execute(_prepare(workspaces, first_id, _EXPERIMENT_SCRIPT, seed=1))
        second = executor.execute(_prepare(workspaces, second_id, _EXPERIMENT_SCRIPT, seed=2))
        assert first.run.spec is not None and second.run.spec is not None
        assert first.run.spec.input_digest != second.run.spec.input_digest

    def test_negative_result_is_terminal_scientific_outcome(
        self, harness: tuple[ExperimentExecutor, FileWorkspaceBackend, SqliteArtifactStore]
    ) -> None:
        executor, workspaces, _ = harness
        run_id = ID("eeeeeeee-2222-4333-8444-555555555555")
        outcome = executor.execute(_prepare(workspaces, run_id, _NEGATIVE_SCRIPT))
        assert outcome.run.state == ExperimentRunState.State.NEGATIVE_RESULT
        assert outcome.run.result is not None
        assert outcome.run.result.failure_reason is not None
        assert "NEGATIVE_RESULT" in outcome.run.result.failure_reason

    def test_timeout_produces_timed_out_run(
        self, harness: tuple[ExperimentExecutor, FileWorkspaceBackend, SqliteArtifactStore]
    ) -> None:
        executor, workspaces, _ = harness
        run_id = ID("ffffffff-2222-4333-8444-555555555555")
        session_id = f"session-{run_id.value[:8]}"
        workspaces.acquire_lease(_WORKSPACE, session_id)
        request = ExperimentExecutionRequest(
            plan=_plan(),
            run_id=run_id,
            command="sleep 60",
            workspace=_WORKSPACE,
            agent_session_id=session_id,
            resource_profile="small",
            timeout_seconds=2,
        )
        outcome = executor.execute(request)
        assert outcome.run.state == ExperimentRunState.State.TIMED_OUT
        assert outcome.run.result is not None
        assert outcome.run.result.failure_reason == "execution timed out"

    def test_workspace_contains_execution_outputs(
        self, harness: tuple[ExperimentExecutor, FileWorkspaceBackend, SqliteArtifactStore]
    ) -> None:
        executor, workspaces, _ = harness
        run_id = ID("99999999-2222-4333-8444-555555555555")
        executor.execute(_prepare(workspaces, run_id, _EXPERIMENT_SCRIPT))
        lease = workspaces.acquire_lease(_WORKSPACE, "session-inspect")
        workspace_dir = workspaces.workspace_dir(lease)
        assert (workspace_dir / "stdout.log").exists()
        assert (workspace_dir / "stderr.log").exists()
        assert (workspace_dir / "experiment_result.json").exists()
        payload = json.loads((workspace_dir / "experiment_result.json").read_text(encoding="utf-8"))
        assert payload["status"] == "SUCCEEDED"
        assert payload["metrics"]["n_samples"] == 5


class TestReproducibilityAuditE2E:
    """真实容器链上的 ReproducibilityAudit 端到端验证。"""

    def test_success_run_produces_pass_audit(
        self, harness: tuple[ExperimentExecutor, FileWorkspaceBackend, SqliteArtifactStore]
    ) -> None:
        executor, workspaces, artifacts = harness
        run_id = ID("10101010-2222-4333-8444-555555555555")
        outcome = executor.execute(_prepare(workspaces, run_id, _EXPERIMENT_SCRIPT))
        audit = build_reproducibility_audit(
            outcome.run,
            audit_id=ID("20202020-2222-4333-8444-555555555555"),
            artifacts=artifacts,
        )
        assert audit.status == "PASS"
        assert verify_reproducibility_audit(audit)
        assert verify_audit_outputs(audit, outcome.run, artifacts) == ()
        assert audit.command == "python experiment.py"
        assert audit.seed == 42
        assert audit.environment_digest is not None
        assert audit.image_digest is not None and audit.image_digest.startswith("sha256:")
        assert audit.workspace_snapshot_before is not None
        assert audit.workspace_snapshot_after is not None
        assert audit.output_artifact_digests
        assert audit.metrics_digest is not None

    def test_negative_result_run_produces_pass_audit(
        self, harness: tuple[ExperimentExecutor, FileWorkspaceBackend, SqliteArtifactStore]
    ) -> None:
        executor, workspaces, artifacts = harness
        run_id = ID("30303030-2222-4333-8444-555555555555")
        outcome = executor.execute(_prepare(workspaces, run_id, _NEGATIVE_SCRIPT))
        assert outcome.run.state == ExperimentRunState.State.NEGATIVE_RESULT
        audit = build_reproducibility_audit(
            outcome.run,
            audit_id=ID("40404040-2222-4333-8444-555555555555"),
            artifacts=artifacts,
        )
        assert audit.status == "PASS"
        assert verify_reproducibility_audit(audit)
        assert verify_audit_outputs(audit, outcome.run, artifacts) == ()
