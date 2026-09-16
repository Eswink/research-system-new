"""M17 WP6a: real GPU Research Slice over the full clean-run chain.

distributed + postgres + requires_docker + requires_gpu. A genuine GPU
worker subprocess (real Docker GPU backend + real startup probe) executes the
M17 experiment through `RemoteExecutionBackend`, and `run_clean_workflow`
drives Objective → Manifest → Task → Scheduler → Remote GPU Worker →
ExecutionBackend → ExperimentRun → Artifact → Evidence → Claim → Evaluation
(m17_gpu_v1 dataset incl. the gpu_compute_device no-fallback scorer) →
UsageLedger (GPU_TIME) → Deliverable.

This is the M17 Definition-of-Done evidence: a real GPU research result that
survives the entire governance chain, with the honest same-host boundary.
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import docker
import pytest
from docker.errors import ImageNotFound

from adapters.execution.remote_backend import RemoteExecutionBackend
from adapters.fakes import FakeBudgetLedger, FakeEvidenceLedger, FakeMemoryStore
from adapters.workspace import FileWorkspaceBackend
from packages.application.m12_reference.clean_run import run_clean_workflow
from packages.application.m12_reference.clean_run_stages import experiment_run_id_of
from packages.application.m12_reference.deps import CleanRunDeps
from packages.application.policy.native import NativePolicyEvaluator
from packages.application.ports import PreflightContext, ProjectSettings
from packages.application.ports.credential_resolver import SecretValue
from packages.domain.enums import EndpointHealth
from packages.domain.workspace import Workspace
from tests.application.m12_clean_run_fixtures import PLAN_ID, catalog, protocol
from tests.distributed.worker_harness import WorkerHarness

pytestmark = [
    pytest.mark.distributed,
    pytest.mark.postgres,
    pytest.mark.requires_docker,
    pytest.mark.requires_gpu,
]

_IMAGE_TAG = "research-os-gpu-sandbox:m17-v1"
_SANDBOX_DIR = Path(__file__).resolve().parents[2] / "adapters" / "execution" / "sandbox"
_EXPERIMENT_SCRIPT = (
    Path(__file__).resolve().parents[2] / "examples" / "experiments" / "m17_gpu_research.py"
)
_RUN_ID = "17171717-2222-4333-8444-555555555555"


class _Credentials:
    def has(self, credential_ref: str) -> bool:
        return True

    def resolve(self, credential_ref: str) -> SecretValue:
        return SecretValue("fixture-secret")


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
        client.images.build(path=str(_SANDBOX_DIR), dockerfile="Dockerfile.gpu", tag=_IMAGE_TAG)
    return _IMAGE_TAG


@pytest.fixture()
def gpu_slice_harness(
    clean_worker_plane: str, tmp_path: Path, gpu_image: str
) -> Generator[tuple[WorkerHarness, CleanRunDeps], None, None]:
    harness = WorkerHarness(clean_worker_plane, lease_ttl_seconds=8, stale_seconds=5.0)
    harness.start_gateway()
    harness.start_schedulers()
    harness.spawn_worker(
        "m17-slice-w1",
        env_extra={
            "RESEARCHOS_WORKER_EXECUTION_BACKEND": "docker",
            "RESEARCHOS_WORKER_GPU_IMAGE": gpu_image,
            "RESEARCHOS_WORKER_DOCKER_IMAGE": gpu_image,
        },
    )
    deps = _slice_deps(harness, tmp_path)
    yield harness, deps
    harness.close()


def _preflight_context() -> PreflightContext:
    from packages.application.ports import CatalogSnapshot

    cat = catalog()
    assert isinstance(cat, CatalogSnapshot)
    assert cat.policy is not None
    project = ProjectSettings(
        project_id="project-m17",
        team_template_id="team",
        default_model_profile_id=None,
        budget_policy_id="budget",
        workspace_backend="workspace",
    )
    return PreflightContext(
        catalog=cat,
        project=project,
        credentials=_Credentials(),
        endpoint_health={"endpoint-1": EndpointHealth.HEALTHY},
        policy_evaluator=NativePolicyEvaluator(cat.policy),
    )


def _slice_deps(harness: WorkerHarness, tmp_path: Path) -> CleanRunDeps:
    from packages.application.ports import CatalogSnapshot

    cat = catalog()
    assert isinstance(cat, CatalogSnapshot)
    context = _preflight_context()
    project = context.project
    workspace_root = tmp_path / "ws-root"
    workspace_root.mkdir(parents=True, exist_ok=True)
    workspaces = FileWorkspaceBackend(tmp_path / "workspaces")
    workspaces.create_workspace(Workspace(id="workspace", name="workspace"))
    # The RemoteExecutionBackend shares the gateway's PG artifact store + job
    # queue — the worker uploads its result bundle there; the backend reads it
    # back. No second truth source.
    execution = RemoteExecutionBackend(job_queue=harness.job_queue, artifacts=harness.gw_artifacts)
    return CleanRunDeps(
        protocol=protocol(),
        catalog=cat,
        project=project,
        context=context,
        execution=execution,
        workspaces=workspaces,
        workspace=Workspace(id="workspace", name="workspace"),
        artifacts=harness.gw_artifacts,
        ledger=FakeEvidenceLedger(),
        memory=FakeMemoryStore(
            allowed_sources=tuple(
                f"{experiment_run_id_of(_RUN_ID)}:{name}"
                for name in ("experiment_result.json", "stdout.log", "stderr.log")
            )
        ),
        budget=FakeBudgetLedger(),
        run_id=_RUN_ID,
        workspace_root=workspace_root,
        experiment_script=str(_EXPERIMENT_SCRIPT),
        resource_profile="gpu-small",
        hypothesis="mixed precision preserves accuracy while improving throughput",
        plan_name="m17-gpu-research",
        dataset_path="examples/eval/datasets/m17_gpu_v1.yaml",
        memory_content="mixed precision (bf16) preserved accuracy and improved throughput on GPU",
    )


def test_gpu_research_slice_full_chain(
    gpu_slice_harness: tuple[WorkerHarness, CleanRunDeps],
) -> None:
    _harness, deps = gpu_slice_harness
    result = run_clean_workflow(
        deps,
        experiment_plan_id=PLAN_ID,
        experiment_command="python experiment.py",
        experiment_timeout_seconds=600,
    )
    # full-chain identifiers all present and cross-linked
    assert result.run_id == _RUN_ID
    assert result.experiment_run_id
    assert result.artifact_ids
    assert result.evidence_ids
    assert result.claim_id
    assert result.audit_status == "PASS"
    assert result.eval_verdict == "PASS"
    assert result.deliverable_digest
    # GPU_TIME budget entry was written (first real consumer of the enum), and
    # its quantity is the real full-workload GPU duration — PART B W-01: the
    # experiment now records the whole training loop (base+candidate), so the
    # ledger quantity must be >= 1s, not the single-batch wall clock (~0s).
    assert result.budget_entries >= 1
    from packages.domain.budget import ResourceType

    entries = deps.budget.snapshot().entries
    gpu_time = [e for e in entries if e.resource_type is ResourceType.GPU_TIME]
    assert gpu_time, "GPU_TIME ledger entry must exist for a real GPU experiment"
    assert any(e.quantity >= 1 for e in gpu_time), (
        f"GPU_TIME quantity must be real full-workload seconds, got "
        f"{[e.quantity for e in gpu_time]}"
    )
