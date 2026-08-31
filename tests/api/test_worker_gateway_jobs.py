"""M16 WP3 worker gateway job routes (claim + result) tests."""

from __future__ import annotations

from typing import Any, cast

from fastapi.testclient import TestClient

from adapters.fakes.artifact_store import FakeArtifactStore
from adapters.fakes.credential_resolver import FakeCredentialResolver
from adapters.fakes.execution_job_queue import FakeExecutionJobQueue
from adapters.fakes.worker_registry import FakeWorkerRegistry
from adapters.fakes.workflow_engine import FakeWorkflowEngine
from packages.domain.core import ID
from packages.domain.enums import TaskKind
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import ResearchTask
from packages.domain.workspace import ExecutionSpec
from services.api.worker_gateway.app import create_worker_app
from services.api.worker_gateway.deps import WorkerGatewayDeps
from services.api.worker_gateway.settings import WorkerGatewaySettings
from tests.contracts.fixtures import task_contract

_ENROLLMENT = "enroll-secret-xyz"


def _as_dict(body: Any) -> dict[str, object]:
    return cast(dict[str, object], body)


def _deps() -> WorkerGatewayDeps:
    return WorkerGatewayDeps(
        registry=FakeWorkerRegistry(),
        credentials=FakeCredentialResolver({"WORKER_ENROLLMENT_SECRET": _ENROLLMENT}),
        settings=WorkerGatewaySettings(enrollment_credential_ref="WORKER_ENROLLMENT_SECRET"),
        workflow=FakeWorkflowEngine(),
        job_queue=FakeExecutionJobQueue(),
        artifacts=FakeArtifactStore(),
    )


def _register(client: TestClient) -> dict[str, object]:
    resp = client.post(
        "/worker/v1/register",
        headers={"X-Worker-Enrollment": _ENROLLMENT},
        json={
            "worker_id": "worker-a",
            "protocol_version": "1",
            "runtime_version": "0.1.0",
            "capabilities": ["docker"],
            "backend_kinds": ["DOCKER"],
            "platform": "linux/amd64",
            "partition_slots": [0],
            "max_concurrency": 1,
        },
    )
    assert resp.status_code == 200
    return _as_dict(resp.json())


def _seed_execution_job(deps: WorkerGatewayDeps) -> str:
    engine = deps.workflow
    assert engine is not None
    task = ResearchTask(
        id=ID.generate(),
        run_id=ID.generate(),
        status=ResearchTaskState.State.QUEUED,
        kind=TaskKind.EXECUTION,
        required_capability="docker",
        partition=0,
    )
    engine.submit(task, task_contract())
    # link the queue descriptor to the same task_id (PG enqueue writes the
    # shared tasks row; the Fake stores them separately)
    deps.job_queue.seed(  # type: ignore[union-attr]
        task.id.value, ExecutionSpec(backend_kind="DOCKER", command="echo hi")
    )
    return task.id.value


def test_claim_returns_job_descriptor() -> None:
    deps = _deps()
    client = TestClient(create_worker_app(deps))
    token = _register(client)["session_token"]
    _seed_execution_job(deps)
    resp = client.post(
        "/worker/v1/claim",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worker_id": "worker-a",
            "registration_generation": 1,
            "capabilities": ["docker"],
            "partitions": [0],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["fence"] == 1
    assert body["lease_id"]
    assert "spec_json" in body


def test_claim_empty_returns_204() -> None:
    deps = _deps()
    client = TestClient(create_worker_app(deps))
    token = _register(client)["session_token"]
    resp = client.post(
        "/worker/v1/claim",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worker_id": "worker-a",
            "registration_generation": 1,
            "capabilities": ["docker"],
            "partitions": [0],
        },
    )
    assert resp.status_code == 204


def test_claim_requires_valid_token() -> None:
    deps = _deps()
    client = TestClient(create_worker_app(deps))
    resp = client.post(
        "/worker/v1/claim",
        headers={"Authorization": "Bearer bogus"},
        json={
            "worker_id": "worker-a",
            "registration_generation": 1,
            "capabilities": ["docker"],
            "partitions": [0],
        },
    )
    assert resp.status_code == 401


def test_result_submission_settles_job() -> None:
    deps = _deps()
    client = TestClient(create_worker_app(deps))
    token = _register(client)["session_token"]
    task_id = _seed_execution_job(deps)
    # claim to obtain a real lease + fence
    claim = client.post(
        "/worker/v1/claim",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worker_id": "worker-a",
            "registration_generation": 1,
            "capabilities": ["docker"],
            "partitions": [0],
        },
    )
    descriptor = claim.json()
    # the Fake job queue needs the lease assigned to accept a result; the
    # gateway's claim path assigns it via the workflow engine, mirror it here
    deps.job_queue.assign(  # type: ignore[union-attr]
        task_id, worker_id="worker-a", lease_id=descriptor["lease_id"], fence=descriptor["fence"]
    )
    resp = client.post(
        f"/worker/v1/tasks/{task_id}/result",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worker_id": "worker-a",
            "registration_generation": 1,
            "lease_id": descriptor["lease_id"],
            "fence": descriptor["fence"],
            "status": "SUCCEEDED",
            "exit_code": 0,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["accepted"] is True


def test_stale_fence_result_rejected() -> None:
    deps = _deps()
    client = TestClient(create_worker_app(deps))
    token = _register(client)["session_token"]
    task_id = _seed_execution_job(deps)
    deps.job_queue.assign(  # type: ignore[union-attr]
        task_id, worker_id="worker-a", lease_id="lease-real", fence=5
    )
    resp = client.post(
        f"/worker/v1/tasks/{task_id}/result",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worker_id": "worker-a",
            "registration_generation": 1,
            "lease_id": "lease-real",
            "fence": 2,  # stale
            "status": "SUCCEEDED",
            "exit_code": 0,
        },
    )
    assert resp.status_code == 409
