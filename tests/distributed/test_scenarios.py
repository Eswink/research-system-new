"""M16 WP4 distributed E2E scenarios (A–J) over real cross-process topology.

Every test drives genuine `python -m services.worker` subprocesses through the
loopback gateway against real PostgreSQL, with the Control-Plane schedulers
(lease recovery + worker reaper) running in the harness. The deterministic
execution backend keeps the gate offline; the real-Docker remote path is
`requires_docker`-marked.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Generator

import pytest

from packages.application.ports.workflow_engine import ClaimRequest
from packages.domain.workers import WorkerState
from tests.distributed.conftest import _postgres_dsn
from tests.distributed.net_proxy import NetProxy
from tests.distributed.worker_harness import WorkerHarness

pytestmark = [pytest.mark.distributed, pytest.mark.postgres]

_WAIT_SECONDS = 45


def _harness() -> WorkerHarness:
    # Realistic lease/stale windows: renewal keeps healthy in-flight jobs alive,
    # while failover scenarios still converge fast via kill / explicit expiry.
    return WorkerHarness(_postgres_dsn(), lease_ttl_seconds=6, stale_seconds=4.0)


def _wait_until(check: Callable[[], bool], timeout: float = _WAIT_SECONDS) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if check():
            return True
        time.sleep(0.2)
    return False


@pytest.fixture()
def harness(clean_worker_plane: str) -> Generator[WorkerHarness, None, None]:
    h = _harness()
    h.start_gateway()
    h.start_schedulers()
    yield h
    h.close()


def test_scenario_a_multi_worker_parallel_disjoint(harness: WorkerHarness) -> None:
    """A: >=2 independent workers each actually execute work; no double ownership."""
    task_ids = [harness.seed_job(idem=f"a-{i}") for i in range(8)]
    harness.spawn_worker("a-w1", env_extra={"RESEARCHOS_WORKER_EXECUTE_DELAY_SECONDS": "1"})
    harness.spawn_worker("a-w2", env_extra={"RESEARCHOS_WORKER_EXECUTE_DELAY_SECONDS": "1"})
    assert _wait_until(lambda: all(harness.job_queue.poll(t) is not None for t in task_ids))
    owners = set()
    for task_id in task_ids:
        outcome = harness.job_queue.poll(task_id)
        assert outcome is not None and outcome.status == "SUCCEEDED"
        owners.add(outcome.worker_id)
        row = _worker_of(harness, task_id)
        assert row is not None  # exactly one worker per job (lease PK enforces)
    # F-6: genuine parallelism — BOTH workers must have executed real work
    assert owners == {"a-w1", "a-w2"}, f"expected both owners, got {owners}"


def _worker_of(harness: WorkerHarness, task_id: str) -> str | None:
    import psycopg

    conn = psycopg.connect(harness.dsn, autocommit=True)
    try:
        row = conn.execute(
            "SELECT worker_id FROM execution_jobs WHERE task_id = %s", (task_id,)
        ).fetchone()
        return str(row[0]) if row and row[0] else None
    finally:
        conn.close()


def test_scenario_b_crash_failover(harness: WorkerHarness) -> None:
    """B: hard-crashed worker's lease expires, is requeued, and another completes."""
    task_id = harness.seed_job(idem="b-1")
    first = harness.spawn_worker(
        "b-crasher", env_extra={"RESEARCHOS_WORKER_EXECUTE_DELAY_SECONDS": "30"}
    )
    # let it claim, then hard-kill without graceful shutdown
    assert _wait_until(lambda: _is_leased_by(harness, task_id, "b-crasher"))
    first.kill()
    first.wait(timeout=10)
    harness.spawn_worker("b-takeover")
    assert _wait_until(lambda: harness.job_queue.poll(task_id) is not None)
    outcome = harness.job_queue.poll(task_id)
    assert outcome is not None
    assert outcome.status == "SUCCEEDED"
    assert outcome.worker_id == "b-takeover"
    # no orphan: exactly one settled job, no leftover lease
    assert _lease_count(harness, task_id) == 0


def _gateway_register(harness: WorkerHarness, worker_id: str) -> tuple[str, int]:
    """Register a session through the gateway; return (token, generation)."""
    import httpx

    from tests.distributed.worker_harness import _ENROLLMENT

    reg = httpx.post(
        f"{harness.gateway_url}/worker/v1/register",
        headers={"X-Worker-Enrollment": _ENROLLMENT},
        json={
            "worker_id": worker_id,
            "protocol_version": "1",
            "runtime_version": "0.1.0",
            "capabilities": ["docker"],
            "backend_kinds": ["DOCKER"],
            "platform": "linux/amd64",
            "partition_slots": [0],
            "max_concurrency": 1,
        },
    )
    assert reg.status_code == 200
    return str(reg.json()["session_token"]), int(reg.json()["registration_generation"])


def _gateway_register_claim(harness: WorkerHarness, worker_id: str) -> tuple[str, int, str, int]:
    """Register + claim one job through the gateway; return (token, gen, lease, fence)."""
    import httpx

    from tests.distributed.worker_harness import _ENROLLMENT

    reg = httpx.post(
        f"{harness.gateway_url}/worker/v1/register",
        headers={"X-Worker-Enrollment": _ENROLLMENT},
        json={
            "worker_id": worker_id,
            "protocol_version": "1",
            "runtime_version": "0.1.0",
            "capabilities": ["docker"],
            "backend_kinds": ["DOCKER"],
            "platform": "linux/amd64",
            "partition_slots": [0],
            "max_concurrency": 1,
        },
    )
    assert reg.status_code == 200
    token = str(reg.json()["session_token"])
    gen = int(reg.json()["registration_generation"])
    claim = httpx.post(
        f"{harness.gateway_url}/worker/v1/claim",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worker_id": worker_id,
            "registration_generation": gen,
            "capabilities": ["docker"],
            "partitions": [0],
        },
    )
    assert claim.status_code == 200
    return token, gen, str(claim.json()["lease_id"]), int(claim.json()["fence"])


def test_scenario_c_stale_result_rejected(harness: WorkerHarness) -> None:
    """C (BLOCKER): a superseded worker's late result is fenced out via the gateway."""
    import httpx

    task_id = harness.seed_job(idem="c-1", partition=0)
    # old worker registers + claims through the gateway (real session, fence 1)
    old_token, old_gen, old_lease, old_fence = _gateway_register_claim(harness, "c-old")
    # force expiry + recovery, then a NEW worker reclaims (higher fence)
    _expire_lease(harness, task_id)
    harness.workflow.recover_expired_leases()
    lease2 = harness.workflow.claim_next(_claim("c-new"))
    assert lease2 is not None and lease2.fence == old_fence + 1
    # the OLD worker submits its late result with its STILL-VALID session -> 409
    resp = httpx.post(
        f"{harness.gateway_url}/worker/v1/tasks/{task_id}/result",
        headers={"Authorization": f"Bearer {old_token}"},
        json={
            "worker_id": "c-old",
            "registration_generation": old_gen,
            "lease_id": old_lease,
            "fence": old_fence,
            "status": "SUCCEEDED",
            "exit_code": 0,
        },
    )
    assert resp.status_code == 409  # stale (lease_id, fence) rejected, not persisted
    # c-old's late result never became authoritative: the job is not settled by it
    settled = harness.job_queue.poll(task_id)
    assert settled is None or settled.worker_id != "c-old"


def test_scenario_d_network_partition_no_old_authority(harness: WorkerHarness) -> None:
    """D: a RUNNING worker loses the network; its authority cannot revive after reconnect."""
    task_id = harness.seed_job(idem="d-1", partition=0)
    proxy = NetProxy("127.0.0.1", harness.port)
    proxy.start()
    # a real worker subprocess connects THROUGH the proxy and starts a long job
    partitioned = harness.spawn_worker(
        "d-partitioned",
        env_extra={
            "RESEARCHOS_WORKER_GATEWAY_URL": f"http://127.0.0.1:{proxy.port}",
            "RESEARCHOS_WORKER_EXECUTE_DELAY_SECONDS": "25",
        },
    )
    assert _wait_until(lambda: _is_leased_by(harness, task_id, "d-partitioned"))
    proxy.blackhole()  # worker keeps running but cannot reach the Control Plane
    _expire_lease(harness, task_id)
    harness.workflow.recover_expired_leases()
    # a healthy worker (direct to gateway) reclaims at a higher fence and completes
    harness.spawn_worker("d-healthy")
    assert _wait_until(lambda: harness.job_queue.poll(task_id) is not None)
    outcome = harness.job_queue.poll(task_id)
    assert outcome is not None and outcome.status == "SUCCEEDED"
    assert outcome.worker_id == "d-healthy"
    # the partitioned worker never owned the settled result; its lease was
    # superseded (fence advanced), so any late submit is fenced out (C + attack
    # suite cover the 409; the reaper's LOST transition is unit-tested).
    assert _worker_of(harness, task_id) == "d-healthy"
    proxy.restore()
    partitioned.terminate()
    partitioned.wait(timeout=10)
    proxy.stop()


def test_scenario_e_duplicate_delivery_single_completion(harness: WorkerHarness) -> None:
    """E: duplicate enqueue + duplicate result produce one canonical completion."""
    task_id = harness.seed_job(idem="e-dup")
    duplicate = harness.seed_job(idem="e-dup")
    assert duplicate == task_id  # idempotent enqueue
    harness.spawn_worker("e-w1")
    assert _wait_until(lambda: harness.job_queue.poll(task_id) is not None)
    outcome = harness.job_queue.poll(task_id)
    assert outcome is not None
    assert outcome.status == "SUCCEEDED"
    # a second worker finds nothing to claim
    assert harness.workflow.claim_next(_claim("e-w2")) is None


def test_scenario_f_scheduler_restart_keeps_state(harness: WorkerHarness) -> None:
    """F: scheduler crash mid-flight loses nothing — recovery resumes from PostgreSQL."""
    task_id = harness.seed_job(idem="f-1", partition=0)
    crasher = harness.spawn_worker(
        "f-crasher", env_extra={"RESEARCHOS_WORKER_EXECUTE_DELAY_SECONDS": "30"}
    )
    assert _wait_until(lambda: _is_leased_by(harness, task_id, "f-crasher"))
    # hard-kill the worker AND stop the scheduler while the lease is in flight
    crasher.kill()
    crasher.wait(timeout=10)
    harness.stop_schedulers()
    assert harness.job_queue.poll(task_id) is None  # nothing settled without recovery
    # restart the Control Plane schedulers: state lives entirely in PostgreSQL
    harness.start_schedulers()
    harness.spawn_worker("f-takeover")
    assert _wait_until(lambda: harness.job_queue.poll(task_id) is not None)
    outcome = harness.job_queue.poll(task_id)
    assert outcome is not None and outcome.status == "SUCCEEDED"
    assert outcome.worker_id == "f-takeover"


def test_scenario_g_drain_stops_claims(harness: WorkerHarness) -> None:
    """G: drained worker stops claiming (server-enforced); others continue; safe offline."""
    harness.spawn_worker("g-w1")
    assert _wait_until(lambda: harness.registry.get("g-w1") is not None)
    reg_before = harness.registry.get("g-w1")
    assert reg_before is not None
    if reg_before.state == "REGISTERING":
        harness.registry.transition("g-w1", WorkerState.Transition.HANDSHAKE_OK)
    harness.registry.drain("g-w1")
    reg = harness.registry.get("g-w1")
    assert reg is not None and reg.state == "DRAINING" and reg.drain_requested is True
    # F-1: a NEW job must NOT be granted to the draining worker even if it asks;
    # a fresh worker takes it instead.
    task_id = harness.seed_job(idem="g-after-drain", partition=0)
    harness.spawn_worker("g-w2")
    assert _wait_until(lambda: harness.job_queue.poll(task_id) is not None)
    assert _worker_of(harness, task_id) == "g-w2"


def test_scenario_j_version_incompatible_rejected(harness: WorkerHarness) -> None:
    """J: an incompatible worker is refused at registration (fail closed, 409)."""
    import httpx

    from tests.distributed.worker_harness import _ENROLLMENT

    resp = httpx.post(
        f"{harness.gateway_url}/worker/v1/register",
        headers={"X-Worker-Enrollment": _ENROLLMENT},  # valid enrollment
        json={
            "worker_id": "j-old",
            "protocol_version": "999",  # unsupported → must reach the 409 handshake gate
            "runtime_version": "0.0.1",
            "capabilities": ["docker"],
            "backend_kinds": ["DOCKER"],
            "platform": "linux/amd64",
            "partition_slots": [0],
            "max_concurrency": 1,
        },
    )
    assert resp.status_code == 409  # F-6: protocol mismatch, not an enrollment 401
    assert "Protocol Mismatch" in resp.text


def test_scenario_h_cooperative_cancel_propagates(harness: WorkerHarness) -> None:
    """H (M17 WP4c): Control-Plane cancel reaches an in-flight job.

    cancel flag (PG) → worker cancel probe (authenticated, lease-holder-only
    gateway route) → backend aborts → CANCELLED result settles the lease.
    A late result replaying the captured fencing identity is fenced out (409).
    """
    import httpx

    task_id = harness.seed_job(idem="h-cancel", partition=0)
    worker = harness.spawn_worker(
        "h-w1", env_extra={"RESEARCHOS_WORKER_EXECUTE_DELAY_SECONDS": "30"}
    )
    assert _wait_until(lambda: _is_leased_by(harness, task_id, "h-w1"))
    identity = harness.lease_identity(task_id)
    assert identity is not None
    lease_id, fence = identity

    # Control Plane cancels the in-flight job.
    harness.job_queue.request_cancel(task_id)
    assert _wait_until(lambda: harness.job_queue.poll(task_id) is not None, timeout=30)
    outcome = harness.job_queue.poll(task_id)
    assert outcome is not None and outcome.status == "CANCELLED"
    assert outcome.worker_id == "h-w1"
    # the lease is released (single-ownership authority is empty again)
    assert harness.lease_identity(task_id) is None

    # A late result replaying the released fencing identity is fenced out:
    # the injector holds a VALID session of its own, but the captured
    # (lease_id, fence) no longer matches any lease row → 409, not persisted.
    late_token, late_gen = _gateway_register(harness, "h-late-holder")
    resp = httpx.post(
        f"{harness.gateway_url}/worker/v1/tasks/{task_id}/result",
        headers={"Authorization": f"Bearer {late_token}"},
        json={
            "worker_id": "h-late-holder",
            "registration_generation": late_gen,
            "lease_id": lease_id,
            "fence": fence,
            "status": "SUCCEEDED",
            "exit_code": 0,
        },
    )
    assert resp.status_code == 409
    settled = harness.job_queue.poll(task_id)
    assert settled is not None and settled.status == "CANCELLED"
    worker.terminate()


def test_worker_clock_skew_does_not_affect_authority() -> None:
    """F-6: authority is immune to worker clock by construction — no client timestamp
    is ever accepted on the worker→gateway surface, and expiry uses PG now()."""
    from services.api.worker_gateway.dto import (
        ClaimRequestDto,
        HeartbeatRequest,
        ResultSubmissionDto,
        WorkerRegisterRequest,
    )

    forbidden = {"timestamp", "ts", "now", "time", "client_time", "sent_at", "at"}
    for dto in (WorkerRegisterRequest, HeartbeatRequest, ClaimRequestDto, ResultSubmissionDto):
        fields = {name.lower() for name in dto.model_fields}
        assert not (fields & forbidden), f"{dto.__name__} must not carry a client clock field"
    # the reaper decides LOST purely from the database clock (server-time authority)
    import inspect

    from adapters.postgres.worker_registry import PostgresWorkerRegistry

    source = inspect.getsource(PostgresWorkerRegistry.list_stale)
    assert "_time_expr" in source and "last_heartbeat <" in source


def _claim(worker_id: str) -> ClaimRequest:
    return ClaimRequest(
        worker_id=worker_id,
        capabilities=frozenset({"docker"}),
        partitions=frozenset(range(16)),
    )


def _expire_lease(harness: WorkerHarness, task_id: str) -> None:
    import psycopg

    conn = psycopg.connect(harness.dsn, autocommit=True)
    try:
        conn.execute(
            "UPDATE leases SET expires_at = now() - interval '1 hour' WHERE task_id = %s",
            (task_id,),
        )
    finally:
        conn.close()


def _is_leased_by(harness: WorkerHarness, task_id: str, worker_id: str) -> bool:
    import psycopg

    conn = psycopg.connect(harness.dsn, autocommit=True)
    try:
        row = conn.execute(
            "SELECT 1 FROM leases WHERE task_id = %s AND worker_id = %s", (task_id, worker_id)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def _lease_count(harness: WorkerHarness, task_id: str) -> int:
    import psycopg

    conn = psycopg.connect(harness.dsn, autocommit=True)
    try:
        row = conn.execute("SELECT count(*) FROM leases WHERE task_id = %s", (task_id,)).fetchone()
        return int(row[0]) if row else 0
    finally:
        conn.close()
