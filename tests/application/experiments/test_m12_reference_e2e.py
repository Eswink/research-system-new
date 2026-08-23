"""M12 Reference 实验真实容器 E2E（requires_docker）。

复用 M9 DockerExecutionBackend + FileWorkspaceBackend + SqliteArtifactStore
生产路径执行 examples/experiments/m12_reference_classification.py，
验证：
- 真实容器内完成双分支对照实验并产出 experiment_result.json；
- ReproducibilityAudit PASS + 输出 digest 一致（同 input+seed+image）；
- NEGATIVE_RESULT / TIMED_OUT 语义保持（沿用 M9 已覆盖，此处重跑回归）；
- 故障注入：容器失败（非零退出）→ ExperimentRun FAILED 且不采信输出。
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
_EXPERIMENT_SCRIPT = (
    Path(__file__).resolve().parents[3]
    / "examples"
    / "experiments"
    / "m12_reference_classification.py"
)

_PLAN_ID = ID("5a1c6a8e-9b2d-4f3a-8c5e-2b2c3d4e5f6a")
_WORKSPACE = Workspace(id="ws-m12", name="ws-m12")


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
        name="m12-reference-classification",
        hypothesis="hash-embedding+linear classifier beats tfidf on low-resource subset",
    ).transition(ExperimentPlanState.Transition.PREREGISTER)


def _prepare(
    workspaces: FileWorkspaceBackend,
    run_id: ID,
    *,
    seed: int | None = 7,
    fail: bool = False,
) -> ExperimentExecutionRequest:
    session_id = f"session-{run_id.value[:8]}"
    lease = workspaces.acquire_lease(_WORKSPACE, session_id)
    workspace_dir = workspaces.workspace_dir(lease)
    script = _EXPERIMENT_SCRIPT.read_text(encoding="utf-8")
    script = script.replace("M12-REFERENCE-RUN", str(run_id.value))
    if fail:
        script += "\nraise SystemExit(1)\n"
    (workspace_dir / "experiment.py").write_text(script, encoding="utf-8")
    return ExperimentExecutionRequest(
        plan=_plan(),
        run_id=run_id,
        command="python experiment.py",
        workspace=_WORKSPACE,
        agent_session_id=session_id,
        seed=seed,
        resource_profile="small",
        timeout_seconds=180,
    )


class TestM12ReferenceExperiment:
    def test_real_container_dual_branch_experiment(
        self, harness: tuple[ExperimentExecutor, FileWorkspaceBackend, SqliteArtifactStore]
    ) -> None:
        executor, workspaces, artifacts = harness
        run_id = ID("12121212-2222-4333-8444-555555555555")
        outcome = executor.execute(_prepare(workspaces, run_id))
        assert outcome.run.state == ExperimentRunState.State.SUCCEEDED
        result = outcome.run.result
        assert result is not None
        assert result.image_digest is not None and result.image_digest.startswith("sha256:")
        assert result.workspace_snapshot_before is not None
        assert result.workspace_snapshot_after is not None
        assert result.metrics_digest is not None
        assert f"{run_id.value}:experiment_result.json" in result.artifact_refs
        assert artifacts.verify(f"{run_id.value}:experiment_result.json")
        payload = json.loads(
            artifacts.get(f"{run_id.value}:experiment_result.json").decode("utf-8")
        )
        assert payload["status"] == "SUCCEEDED"
        assert "baseline" in payload["results"] and "candidate" in payload["results"]
        assert "accuracy" in payload["results"]["baseline"]["metrics"]
        assert "accuracy" in payload["results"]["candidate"]["metrics"]

    def test_same_input_same_output_digest(
        self, harness: tuple[ExperimentExecutor, FileWorkspaceBackend, SqliteArtifactStore]
    ) -> None:
        executor, workspaces, artifacts = harness
        first_id = ID("23232323-2222-4333-8444-555555555555")
        second_id = ID("24242424-2222-4333-8444-555555555555")
        first = executor.execute(_prepare(workspaces, first_id))
        second = executor.execute(_prepare(workspaces, second_id))
        assert first.run.spec is not None and second.run.spec is not None
        assert first.run.spec.input_digest == second.run.spec.input_digest
        assert first.run.result is not None and second.run.result is not None
        assert first.run.result.image_digest == second.run.result.image_digest
        first_payload = json.loads(
            artifacts.get(f"{first_id.value}:experiment_result.json").decode("utf-8")
        )
        second_payload = json.loads(
            artifacts.get(f"{second_id.value}:experiment_result.json").decode("utf-8")
        )
        # experiment_run_id 每次不同；科学结果必须一致；
        # feature_time_s 为 wall-clock 测量（合理非确定性，测量并记录，不用于复现断言）
        for branch in ("baseline", "candidate"):
            assert (
                first_payload["results"][branch]["metrics"]
                == second_payload["results"][branch]["metrics"]
            )
        assert (
            first_payload["metrics"]["baseline_accuracy"]
            == second_payload["metrics"]["baseline_accuracy"]
        )
        assert (
            first_payload["metrics"]["candidate_accuracy"]
            == second_payload["metrics"]["candidate_accuracy"]
        )

    def test_reproducibility_audit_pass_and_outputs_verified(
        self, harness: tuple[ExperimentExecutor, FileWorkspaceBackend, SqliteArtifactStore]
    ) -> None:
        executor, workspaces, artifacts = harness
        run_id = ID("35353535-2222-4333-8444-555555555555")
        outcome = executor.execute(_prepare(workspaces, run_id))
        audit = build_reproducibility_audit(
            outcome.run,
            audit_id=ID("46464646-2222-4333-8444-555555555555"),
            artifacts=artifacts,
        )
        assert audit.status == "PASS"
        assert verify_reproducibility_audit(audit)
        assert verify_audit_outputs(audit, outcome.run, artifacts) == ()
        assert audit.command == "python experiment.py"
        assert audit.seed == 7
        assert audit.environment_digest is not None
        assert audit.image_digest is not None and audit.image_digest.startswith("sha256:")
        assert audit.workspace_snapshot_before is not None
        assert audit.workspace_snapshot_after is not None
        assert audit.output_artifact_digests
        assert audit.metrics_digest is not None

    def test_failing_command_is_failed_not_negative(
        self, harness: tuple[ExperimentExecutor, FileWorkspaceBackend, SqliteArtifactStore]
    ) -> None:
        executor, workspaces, _ = harness
        run_id = ID("57575757-2222-4333-8444-555555555555")
        outcome = executor.execute(_prepare(workspaces, run_id, fail=True))
        assert outcome.run.state == ExperimentRunState.State.FAILED
        assert outcome.run.result is not None
        assert outcome.run.result.failure_reason is not None

    def test_timeout_is_timed_out(
        self, harness: tuple[ExperimentExecutor, FileWorkspaceBackend, SqliteArtifactStore]
    ) -> None:
        executor, workspaces, _ = harness
        run_id = ID("68686868-2222-4333-8444-555555555555")
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


class TestM12ReferenceNegativeResult:
    def test_negative_result_stays_scientific(
        self, harness: tuple[ExperimentExecutor, FileWorkspaceBackend, SqliteArtifactStore]
    ) -> None:
        """科学负结论（exit 0 + 声明 NEGATIVE_RESULT）≠ 系统失败。"""
        executor, workspaces, _ = harness
        run_id = ID("79797979-2222-4333-8444-555555555555")
        session_id = f"session-{run_id.value[:8]}"
        lease = workspaces.acquire_lease(_WORKSPACE, session_id)
        workspace_dir = workspaces.workspace_dir(lease)
        script = (
            "import json\n"
            "payload = {'experiment_run_id': 'RUN', 'status': 'NEGATIVE_RESULT',\n"
            "           'artifact_refs': [], 'metrics': {'effect_size': 0.02},\n"
            "           'failure_ref': 'no significant improvement'}\n"
            "open('experiment_result.json', 'w').write(json.dumps(payload))\n"
        ).replace("'RUN'", repr(str(run_id.value)))
        (workspace_dir / "experiment.py").write_text(script, encoding="utf-8")
        outcome = executor.execute(
            ExperimentExecutionRequest(
                plan=_plan(),
                run_id=run_id,
                command="python experiment.py",
                workspace=_WORKSPACE,
                agent_session_id=session_id,
                seed=7,
                resource_profile="small",
                timeout_seconds=60,
            )
        )
        assert outcome.run.state == ExperimentRunState.State.NEGATIVE_RESULT
        result = outcome.run.result
        assert result is not None
        assert result.failure_reason is not None
        assert "NEGATIVE_RESULT" in result.failure_reason
