"""M17 WP2 GPU scheduling contract suite (Fake / SQLite / PostgreSQL).

Scheduling-key semantics: the single token `gpu` in `tasks.required_capability`.
- A GPU-required task is NEVER claimable by CPU-only capabilities.
- A CPU task's requirement is never relaxed or upgraded because GPU
  capabilities exist in the system.
- GPU capability alone cannot claim CPU work (no accidental widening).
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from packages.application.ports.workflow_engine import ClaimRequest, WorkflowEngine
from packages.domain.core import ID
from packages.domain.enums import TaskKind
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import ResearchTask
from tests.contracts.fixtures import task_contract
from tests.contracts.registry import PORT_IMPLEMENTATIONS

_FACTORIES: list[Callable[[], object]] = list(PORT_IMPLEMENTATIONS["workflow_engine"])


def _execution_task(capability: str | None) -> ResearchTask:
    return ResearchTask(
        id=ID.generate(),
        run_id=ID.generate(),
        status=ResearchTaskState.State.QUEUED,
        kind=TaskKind.EXECUTION,
        required_capability=capability,
        partition=0,
    )


def _request(capabilities: frozenset[str]) -> ClaimRequest:
    return ClaimRequest(
        worker_id="w1", capabilities=capabilities, partitions=frozenset({0})
    )


@pytest.mark.parametrize("factory", _FACTORIES)
def test_gpu_task_never_claimed_by_cpu_only_capabilities(
    factory: Callable[[], object],
) -> None:
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    task = _execution_task("gpu")
    engine.submit(task, task_contract())
    # Never claimed: every CPU-only claim finds nothing (a second claim after
    # the first also returns None — the task was never leased or consumed).
    assert engine.claim_next(_request(frozenset({"docker"}))) is None
    assert engine.claim_next(_request(frozenset({"cpu", "docker"}))) is None
    # and the task is still there for the right worker (not consumed/lost):
    assert engine.claim_next(_request(frozenset({"docker", "gpu"}))) is not None


@pytest.mark.parametrize("factory", _FACTORIES)
def test_gpu_task_claimed_by_gpu_capable_worker(factory: Callable[[], object]) -> None:
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    task = _execution_task("gpu")
    engine.submit(task, task_contract())
    lease = engine.claim_next(_request(frozenset({"docker", "gpu"})))
    assert lease is not None
    assert lease.task_id == task.id.value
    assert lease.fence == 1


@pytest.mark.parametrize("factory", _FACTORIES)
def test_gpu_task_partition_relax_still_respects_capability(
    factory: Callable[[], object],
) -> None:
    """The starvation fallback (relax_partitions) must NOT relax capability."""
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    task = _execution_task("gpu")
    engine.submit(task, task_contract())
    request = ClaimRequest(
        worker_id="w1",
        capabilities=frozenset({"docker"}),
        partitions=frozenset({1, 2}),
        relax_partitions=True,
    )
    assert engine.claim_next(request) is None


@pytest.mark.parametrize("factory", _FACTORIES)
def test_cpu_task_requirement_not_upgraded_by_gpu_presence(
    factory: Callable[[], object],
) -> None:
    """A CPU task keeps its `docker` requirement — a GPU-capable worker
    (docker+gpu) claims it, and GPU capability alone still cannot."""
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    task = _execution_task("docker")
    engine.submit(task, task_contract())
    assert engine.claim_next(_request(frozenset({"gpu"}))) is None
    lease = engine.claim_next(_request(frozenset({"docker", "gpu"})))
    assert lease is not None and lease.task_id == task.id.value


@pytest.mark.parametrize("factory", _FACTORIES)
def test_gpu_capability_alone_cannot_claim_cpu_task(
    factory: Callable[[], object],
) -> None:
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    engine.submit(_execution_task("docker"), task_contract())
    assert engine.claim_next(_request(frozenset({"gpu"}))) is None


@pytest.mark.parametrize("factory", _FACTORIES)
def test_null_capability_task_stays_claimable_by_any_worker(
    factory: Callable[[], object],
) -> None:
    """Pre-M17 semantics preserved: NULL requirement matches any worker,
    including a GPU-capable one (CPU task is never forced onto GPU-only)."""
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    engine.submit(_execution_task(None), task_contract())
    assert engine.claim_next(_request(frozenset({"gpu"}))) is not None
