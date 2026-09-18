"""M16 WP2 claim_next + fencing contract suite (Fake / SQLite / PostgreSQL).

Proves the shared scheduling semantics across all three WorkflowEngine
implementations: capability/partition claim filtering, fence advancement,
single ownership per task, AGENT_SESSION immunity from remote claims, and
stale-fence completion rejection.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import fields, replace

import pytest

from packages.application.ports.errors import InvalidInputError
from packages.application.ports.workflow_engine import (
    ClaimRequest,
    TaskCompletion,
    TaskLease,
    WorkflowEngine,
)
from packages.domain.core import ID
from packages.domain.enums import TaskKind
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import ResearchTask
from tests.contracts.fixtures import task_contract
from tests.contracts.registry import PORT_IMPLEMENTATIONS

_FACTORIES: list[Callable[[], object]] = list(PORT_IMPLEMENTATIONS["workflow_engine"])


def _execution_task(
    *,
    capability: str | None = "docker",
    partition: int | None = 0,
) -> ResearchTask:
    return ResearchTask(
        id=ID.generate(),
        run_id=ID.generate(),
        status=ResearchTaskState.State.QUEUED,
        kind=TaskKind.EXECUTION,
        required_capability=capability,
        partition=partition,
    )


def _request(worker_id: str = "w1", **overrides: object) -> ClaimRequest:
    base: dict[str, object] = {
        "worker_id": worker_id,
        "capabilities": frozenset({"docker"}),
        "partitions": frozenset({0}),
    }
    base.update(overrides)
    return ClaimRequest(**base)  # type: ignore[arg-type]


def _with_fence(lease: TaskLease, *, fence: int) -> TaskLease:
    return replace(lease, fence=fence)


def test_claim_request_declares_no_lease_ttl_field() -> None:
    """GOAL-005 cycle 3 = EC-03: no declaration without a consumer.

    `ClaimRequest.lease_ttl_seconds` used to sit here (default 300, with a
    `>= 1` check) while all three implementations leased with the *engine*
    TTL and no call site passed the field — a false affordance. It was
    removed rather than given invented semantics. Re-introducing per-claim
    TTL takes a real reader plus the same documents updated; this case going
    red is that reminder, not a bug.
    """
    assert "lease_ttl_seconds" not in {item.name for item in fields(ClaimRequest)}


@pytest.mark.parametrize("factory", _FACTORIES)
def test_claim_next_empty_returns_none(factory: Callable[[], object]) -> None:
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    assert engine.claim_next(_request()) is None


@pytest.mark.parametrize("factory", _FACTORIES)
def test_claim_next_leases_matching_execution(factory: Callable[[], object]) -> None:
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    task = _execution_task()
    engine.submit(task, task_contract())
    lease = engine.claim_next(_request())
    assert lease is not None
    assert lease.task_id == task.id.value
    assert lease.worker_id == "w1"
    assert lease.fence == 1


@pytest.mark.parametrize("factory", _FACTORIES)
def test_claim_next_respects_capability(factory: Callable[[], object]) -> None:
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    engine.submit(_execution_task(capability="gpu"), task_contract())
    assert engine.claim_next(_request(capabilities=frozenset({"docker"}))) is None
    lease = engine.claim_next(_request(capabilities=frozenset({"gpu", "docker"})))
    assert lease is not None


@pytest.mark.parametrize("factory", _FACTORIES)
def test_claim_next_respects_partition(factory: Callable[[], object]) -> None:
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    engine.submit(_execution_task(partition=7), task_contract())
    assert engine.claim_next(_request(partitions=frozenset({0}))) is None
    # starvation fallback: capability-only match ignores partition
    lease = engine.claim_next(_request(partitions=frozenset({0}), relax_partitions=True))
    assert lease is not None


@pytest.mark.parametrize("factory", _FACTORIES)
def test_agent_session_never_claimed_by_worker(factory: Callable[[], object]) -> None:
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    engine.submit(ResearchTask(id=ID.generate(), run_id=ID.generate()), task_contract())
    assert engine.claim_next(_request()) is None


@pytest.mark.parametrize("factory", _FACTORIES)
def test_second_claim_of_leased_task_returns_none(factory: Callable[[], object]) -> None:
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    engine.submit(_execution_task(), task_contract())
    first = engine.claim_next(_request(worker_id="w1"))
    assert first is not None
    assert engine.claim_next(_request(worker_id="w2")) is None


@pytest.mark.parametrize("factory", _FACTORIES)
def test_stale_fence_completion_rejected(factory: Callable[[], object]) -> None:
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    task = _execution_task()
    engine.submit(task, task_contract())
    lease = engine.claim_next(_request())
    assert lease is not None
    stale = _with_fence(lease, fence=lease.fence + 99)
    with pytest.raises(InvalidInputError):
        engine.complete(stale, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))


@pytest.mark.parametrize("factory", _FACTORIES)
def test_valid_fence_completion_succeeds(factory: Callable[[], object]) -> None:
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    task = _execution_task()
    engine.submit(task, task_contract())
    lease = engine.claim_next(_request())
    assert lease is not None
    engine.complete(lease, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))


@pytest.mark.parametrize("factory", _FACTORIES)
def test_renew_lease_preserves_identity_and_rejects_stale(factory: Callable[[], object]) -> None:
    """F-7: renew extends the SAME (lease_id, fence); a superseded triple fails."""
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    task = _execution_task()
    engine.submit(task, task_contract())
    lease = engine.claim_next(_request(worker_id="w1"))
    assert lease is not None
    # matching triple renews cleanly (no rotation of lease_id/fence)
    engine.renew_lease(task.id.value, lease.lease_id, lease.fence, "w1")
    # wrong worker / wrong fence cannot renew someone else's lease
    with pytest.raises(InvalidInputError):
        engine.renew_lease(task.id.value, lease.lease_id, lease.fence, "intruder")
    with pytest.raises(InvalidInputError):
        engine.renew_lease(task.id.value, lease.lease_id, lease.fence + 5, "w1")
