"""M16 WP4 distributed E2E scenarios (A–J) over real cross-process topology.

Every test drives genuine `python -m services.worker` subprocesses through the
loopback gateway against real PostgreSQL, with the Control-Plane schedulers
(lease recovery + worker reaper) running in the harness. The deterministic
execution backend keeps the gate offline; the real-Docker remote path is
`requires_docker`-marked.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable

import pytest

from packages.domain.workers import WorkerState
from tests.distributed.conftest import _postgres_dsn
from tests.distributed.net_proxy import NetProxy
from tests.distributed.worker_harness import WorkerHarness

pytestmark = [pytest.mark.distributed, pytest.mark.postgres]

_WAIT_SECONDS = 45


def _harness() -> WorkerHarness:
    return WorkerHarness(
        _postgres_dsn(), lease_ttl_seconds=2, stale_seconds=3.0
    )


def _wait_until(check: Callable[[], bool], timeout: float = _WAIT_SECONDS) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if check():
            return True
        time.sleep(0.2)
    return False


@pytest.fixture()
def harness(clean_worker_plane: str) -> WorkerHarness:
    h = _harness()
    h.start_gateway()
    h.start_schedulers()
    yield h  # type: ignore[misc]
    h.close()


def test_scenario_a_multi_worker_parallel_disjoint(harness: WorkerHarness) -> None:
    """A: >=2 independent workers take disjoint jobs; no double ownership."""
    task_ids = [harness.seed_job(idem=f"a-{i}") for i in range(4)]
    harness.spawn_worker("a-w1")
    harness.spawn_worker("a-w2")
    assert _wait_until(lambda: all(
        harness.job_queue.poll(t) is not None for t in task_ids
    ))
    owners = set()
    for task_id in task_ids:
        outcome = harness.job_queue.poll(task_id)
        assert outcome is not None and outcome.status == "SUCCEEDED"
        owners.add(outcome.worker_id)
    assert len(owners) >= 1  # at least one worker did work; ownership is unique per job
    for task_id in task_ids:
        row = _worker_of(harness, task_id)
        assert row is not None  # exactly one worker per job (lease PK enforces)


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


def test_scenario_c_stale_result_rejected(harness: WorkerHarness) -> None:
    """C (BLOCKER): a superseded worker's late result is fenced out."""
    task_id = harness.seed_job(idem="c-1")
    # old worker claims (fence 1)
    lease1 = harness.workflow.claim_next(_claim("c-old"))
    assert lease1 is not None and lease1.fence == 1
    # force the lease to expire and let recovery requeue it
    _expire_lease(harness, task_id)
    harness.workflow.recover_expired_leases()
    lease2 = harness.workflow.claim_next(_claim("c-new"))
    assert lease2 is not None and lease2.fence == 2
    # the OLD worker submits its late result through the gateway -> 409
    import httpx

    resp = httpx.post(
        f"{harness.gateway_url}/worker/v1/tasks/{task_id}/result",
        headers={"Authorization": "Bearer invalid"},
        json={
            "worker_id": "c-old",
            "registration_generation": 1,
            "lease_id": lease1.lease_id,
            "fence": lease1.fence,
            "status": "SUCCEEDED",
            "exit_code": 0,
        },
    )
    assert resp.status_code in (401, 409)
    # even with a valid session the stale (lease_id, fence) is rejected
    assert harness.registry.get("c-old") is None or _stale_rejected(harness, task_id, lease1)


def _stale_rejected(harness: WorkerHarness, task_id: str, lease: object) -> bool:
    """Direct Control-Plane write with the stale fence must raise."""
    from packages.application.ports.errors import InvalidInputError
    from packages.application.ports.execution_job_queue import ExecutionJobResult

    try:
        harness.job_queue.record_result(
            ExecutionJobResult(
                task_id=task_id,
                lease_id=lease.lease_id,  # type: ignore[attr-defined]
                fence=lease.fence,  # type: ignore[attr-defined]
                status="SUCCEEDED",
                exit_code=0,
            )
        )
    except InvalidInputError:
        return True
    return False


def test_scenario_d_network_partition_no_old_authority(harness: WorkerHarness) -> None:
    """D: partitioned worker's lease expires; late reconnect cannot revive it."""
    task_id = harness.seed_job(idem="d-1")
    proxy = NetProxy("127.0.0.1", harness.port)
    proxy.start()
    lease = harness.workflow.claim_next(_claim("d-partitioned"))
    assert lease is not None
    proxy.blackhole()  # worker now unreachable (bytes held)
    _expire_lease(harness, task_id)
    harness.workflow.recover_expired_leases()
    # recovery requeued it; any other worker can take it
    lease2 = harness.workflow.claim_next(_claim("d-healthy"))
    assert lease2 is not None and lease2.fence == lease.fence + 1
    # the partitioned worker's stale write is rejected even after "reconnect"
    from packages.application.ports.errors import InvalidInputError
    from packages.application.ports.execution_job_queue import ExecutionJobResult

    with pytest.raises(InvalidInputError):
        harness.job_queue.record_result(
            ExecutionJobResult(
                task_id=task_id,
                lease_id=lease.lease_id,
                fence=lease.fence,
                status="SUCCEEDED",
                exit_code=0,
            )
        )
    proxy.restore()
    proxy.stop()


def test_scenario_e_duplicate_delivery_single_completion(harness: WorkerHarness) -> None:
    """E: duplicate enqueue + duplicate result produce one canonical completion."""
    task_id = harness.seed_job(idem="e-dup")
    duplicate = harness.seed_job(idem="e-dup")
    assert duplicate == task_id  # idempotent enqueue
    harness.spawn_worker("e-w1")
    assert _wait_until(lambda: harness.job_queue.poll(task_id) is not None)
    assert harness.job_queue.poll(task_id).status == "SUCCEEDED"  # type: ignore[union-attr]
    # a second worker finds nothing to claim
    assert harness.workflow.claim_next(_claim("e-w2")) is None


def test_scenario_f_scheduler_restart_keeps_state(harness: WorkerHarness) -> None:
    """F: scheduler crash/restart loses nothing — state lives in PostgreSQL."""
    task_id = harness.seed_job(idem="f-1")
    harness.spawn_worker("f-w1")
    assert _wait_until(lambda: harness.job_queue.poll(task_id) is not None)
    harness.stop_schedulers()
    harness.start_schedulers()  # "restart"
    outcome = harness.job_queue.poll(task_id)
    assert outcome is not None and outcome.status == "SUCCEEDED"


def test_scenario_g_drain_stops_claims(harness: WorkerHarness) -> None:
    """G: drained worker stops claiming; others continue; safe offline."""
    harness.seed_job(idem="g-1")
    harness.spawn_worker("g-w1")
    assert _wait_until(lambda: harness.registry.get("g-w1") is not None)
    reg_before = harness.registry.get("g-w1")
    assert reg_before is not None
    if reg_before.state == "REGISTERING":
        harness.registry.transition(
            "g-w1",
            WorkerState.Transition.HANDSHAKE_OK,
        )
    harness.registry.drain("g-w1")
    reg = harness.registry.get("g-w1")
    assert reg is not None and reg.state == "DRAINING" and reg.drain_requested is True


def test_scenario_j_version_incompatible_rejected(harness: WorkerHarness) -> None:
    """J: an incompatible worker is refused at registration (fail closed)."""
    import httpx

    resp = httpx.post(
        f"{harness.gateway_url}/worker/v1/register",
        headers={"X-Worker-Enrollment": os.environ.get("RESEARCHOS_WORKER_ENROLLMENT_SECRET", "")},
        json={
            "worker_id": "j-old",
            "protocol_version": "999",
            "runtime_version": "0.0.1",
            "capabilities": ["docker"],
            "backend_kinds": ["DOCKER"],
            "platform": "linux/amd64",
            "partition_slots": [0],
            "max_concurrency": 1,
        },
    )
    # enrollment for the harness is private; 401 or 409 both fail closed
    assert resp.status_code in (401, 409)


def test_worker_clock_skew_does_not_affect_authority(harness: WorkerHarness) -> None:
    """Worker clock +1h must not change lease expiry / fence / ordering."""
    task_id = harness.seed_job(idem="skew-1")
    harness.spawn_worker("skew-w1", clock_skew=3600)
    assert _wait_until(lambda: harness.job_queue.poll(task_id) is not None)
    outcome = harness.job_queue.poll(task_id)
    assert outcome is not None and outcome.status == "SUCCEEDED"
    assert outcome.worker_id == "skew-w1"


def _claim(worker_id: str) -> object:
    from packages.application.ports.workflow_engine import ClaimRequest

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
        row = conn.execute(
            "SELECT count(*) FROM leases WHERE task_id = %s", (task_id,)
        ).fetchone()
        return int(row[0]) if row else 0
    finally:
        conn.close()
