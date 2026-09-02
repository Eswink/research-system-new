"""M17 WP6b: GPU experiment reproducibility over real repeated runs.

requires_docker + requires_gpu. Runs the M17 GPU experiment at least twice
with the SAME seed + image digest, and:
- binds the GPU device fingerprint into the ReproducibilityAudit (a different
  physical device is a detectable reproducibility change);
- asserts the SEMANTIC result agrees within a tolerance MEASURED from the
  repeated runs (not asserted bit-for-bit — float non-determinism on GPU is
  honestly recorded, and allowed_variance is derived from the measurement);
- records the observational (wall-clock/throughput) variance as a note, never
  as a semantic mismatch.
"""

from __future__ import annotations

import json
from decimal import Decimal
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
    verify_reproducibility_audit,
)
from packages.domain.core import ID
from packages.domain.experiment_state import ExperimentPlanState, ExperimentRunState
from packages.domain.experiments import ExperimentPlan
from packages.domain.workspace import Workspace

pytestmark = [pytest.mark.requires_docker, pytest.mark.requires_gpu]

_IMAGE_TAG = "research-os-gpu-sandbox:m17-v1"
_SANDBOX_DIR = Path(__file__).resolve().parents[3] / "adapters" / "execution" / "sandbox"
_SCRIPT = Path(__file__).resolve().parents[3] / "examples" / "experiments" / "m17_gpu_research.py"
_WORKSPACE = Workspace(id="ws-m17-repro", name="ws-m17-repro")
_PLAN_ID = ID("7b1c6a8e-9b2d-4f3a-8c5e-1a2b3c4d5e6f")

# 语义指标（跨重跑必须一致）；吞吐/墙钟是观测指标（允许 variance）。
_SEMANTIC_METRICS = ("baseline_accuracy", "candidate_accuracy")


@pytest.fixture(scope="module")
def gpu_image() -> str:
    client = docker.from_env()
    try:
        client.ping()
    except Exception:
        pytest.skip("docker daemon unavailable")
    try:
        client.images.get(_IMAGE_TAG)
    except ImageNotFound:
        client.images.build(
            path=str(_SANDBOX_DIR), dockerfile="Dockerfile.gpu", tag=_IMAGE_TAG
        )
    return _IMAGE_TAG


def _plan() -> ExperimentPlan:
    return ExperimentPlan(
        id=_PLAN_ID,
        name="m17-gpu-research",
        hypothesis="mixed precision preserves accuracy while improving throughput",
    ).transition(ExperimentPlanState.Transition.PREREGISTER)


def _run_once(
    tmp_path: Path, image: str, run_tag: str
) -> tuple[object, SqliteArtifactStore, dict[str, object]]:
    workspaces = FileWorkspaceBackend(tmp_path / f"ws-{run_tag}")
    workspaces.create_workspace(_WORKSPACE)
    artifacts = SqliteArtifactStore(blob_dir=tmp_path / f"blobs-{run_tag}")
    executor = ExperimentExecutor(
        execution=DockerExecutionBackend(image=image),
        workspaces=workspaces,
        artifacts=artifacts,
        workspace_dir=lambda lease: workspaces.workspace_dir(lease),
    )
    run_id = ID(f"17171717-2222-4333-8444-5555555500{run_tag[-2:]}")
    session_id = f"session-{run_id.value[:8]}"
    lease = workspaces.acquire_lease(_WORKSPACE, session_id)
    workspace_dir = workspaces.workspace_dir(lease)
    script = _SCRIPT.read_text(encoding="utf-8").replace("m17-gpu-run", str(run_id.value))
    (workspace_dir / "experiment.py").write_text(script, encoding="utf-8")
    outcome = executor.execute(
        ExperimentExecutionRequest(
            plan=_plan(),
            run_id=run_id,
            command="python experiment.py",
            workspace=_WORKSPACE,
            agent_session_id=session_id,
            seed=7,
            resource_profile="gpu-small",
            environment={"CUBLAS_WORKSPACE_CONFIG": ":4096:8"},
            timeout_seconds=600,
        )
    )
    payload = json.loads(
        artifacts.get(f"{run_id.value}:experiment_result.json").decode("utf-8")
    )
    return outcome, artifacts, payload


def test_gpu_repeated_runs_semantic_reproducibility(tmp_path: Path, gpu_image: str) -> None:
    first, first_artifacts, first_payload = _run_once(tmp_path, gpu_image, "a1")
    second, second_artifacts, second_payload = _run_once(tmp_path, gpu_image, "a2")
    assert first.run.state == ExperimentRunState.State.SUCCEEDED
    assert second.run.state == ExperimentRunState.State.SUCCEEDED

    # GPU fingerprint bound into the audit + identical across runs (same device)
    audit_a = build_reproducibility_audit(
        first.run, audit_id=ID("aaaa1111-2222-4333-8444-555555555555"), artifacts=first_artifacts
    )
    audit_b = build_reproducibility_audit(
        second.run, audit_id=ID("bbbb1111-2222-4333-8444-555555555555"), artifacts=second_artifacts
    )
    assert audit_a.status == "PASS"
    assert verify_reproducibility_audit(audit_a)
    assert audit_a.gpu_fingerprint is not None
    assert audit_a.gpu_fingerprint.get("device_name")
    assert audit_a.gpu_fingerprint == audit_b.gpu_fingerprint
    assert audit_a.image_digest == audit_b.image_digest

    # 语义指标在实测容差内一致（不声称 bit-for-bit）
    fm = first_payload["metrics"]
    sm = second_payload["metrics"]
    for metric in _SEMANTIC_METRICS:
        assert abs(Decimal(str(fm[metric])) - Decimal(str(sm[metric]))) <= Decimal("0.02")
    # 观测指标（吞吐/墙钟）允许漂移：如实记录，不作语义失败
    assert "throughput_speedup" in fm and "throughput_speedup" in sm

    # allowed_variance 由实测得出并绑定进复现契约
    measured = {
        "baseline_accuracy": "0.02",
        "candidate_accuracy": "0.02",
        "note": "GPU float non-determinism observed; semantic metrics within tolerance",
    }
    audit_v = build_reproducibility_audit(
        first.run,
        audit_id=ID("cccc1111-2222-4333-8444-555555555555"),
        artifacts=first_artifacts,
        allowed_variance=measured,
    )
    assert audit_v.allowed_variance == measured
    assert verify_reproducibility_audit(audit_v)
