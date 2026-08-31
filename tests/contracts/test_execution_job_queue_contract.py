"""M16 WP3 ExecutionJobQueue contract suite (Fake + PostgreSQL)."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from packages.application.ports.errors import InvalidInputError
from packages.application.ports.execution_job_queue import (
    ExecutionJobQueue,
    ExecutionJobRequest,
    ExecutionJobResult,
)
from packages.domain.core import ID
from packages.domain.workspace import ExecutionSpec
from tests.contracts.registry import PORT_IMPLEMENTATIONS

_FACTORIES: list[Callable[[], object]] = list(PORT_IMPLEMENTATIONS["execution_job_queue"])


def _request(idem: str = "idem-1") -> ExecutionJobRequest:
    return ExecutionJobRequest(
        spec=ExecutionSpec(backend_kind="DOCKER", command="echo hi"),
        run_id=ID.generate().value,
        capability="docker",
        idempotency_key=idem,
        input_bundle_digest="sha256:abc",
        partition=3,
    )


@pytest.mark.parametrize("factory", _FACTORIES)
def test_enqueue_returns_task_id(factory: Callable[[], object]) -> None:
    queue: ExecutionJobQueue = factory()  # type: ignore[assignment]
    task_id = queue.enqueue(_request())
    assert task_id
    assert queue.poll(task_id) is None  # still in flight


@pytest.mark.parametrize("factory", _FACTORIES)
def test_enqueue_is_idempotent_on_key(factory: Callable[[], object]) -> None:
    queue: ExecutionJobQueue = factory()  # type: ignore[assignment]
    first = queue.enqueue(_request("same-key"))
    second = queue.enqueue(_request("same-key"))
    assert first == second


@pytest.mark.parametrize("factory", _FACTORIES)
def test_cancel_flag_roundtrip(factory: Callable[[], object]) -> None:
    queue: ExecutionJobQueue = factory()  # type: ignore[assignment]
    task_id = queue.enqueue(_request("cancel-1"))
    assert queue.cancel_requested(task_id) is False
    queue.request_cancel(task_id)
    assert queue.cancel_requested(task_id) is True


def test_fake_record_result_requires_matching_lease() -> None:
    from adapters.fakes.execution_job_queue import FakeExecutionJobQueue

    queue = FakeExecutionJobQueue()
    task_id = queue.enqueue(_request("fake-lease"))
    # no lease assigned yet -> rejected
    with pytest.raises(InvalidInputError):
        queue.record_result(
            ExecutionJobResult(
                task_id=task_id, lease_id="l1", fence=1, status="SUCCEEDED", exit_code=0
            )
        )
    queue.assign(task_id, worker_id="w1", lease_id="l1", fence=1)
    queue.record_result(
        ExecutionJobResult(
            task_id=task_id, lease_id="l1", fence=1, status="SUCCEEDED", worker_id="w1", exit_code=0
        )
    )
    outcome = queue.poll(task_id)
    assert outcome is not None and outcome.status == "SUCCEEDED"


def test_fake_record_result_rejects_non_terminal_status() -> None:
    """Untrusted worker status cannot resurrect a job as QUEUED (reviewer major)."""
    from adapters.fakes.execution_job_queue import FakeExecutionJobQueue

    queue = FakeExecutionJobQueue()
    task_id = queue.enqueue(_request("fake-status"))
    queue.assign(task_id, worker_id="w1", lease_id="l1", fence=1)
    with pytest.raises(InvalidInputError):
        queue.record_result(
            ExecutionJobResult(
                task_id=task_id,
                lease_id="l1",
                fence=1,
                status="QUEUED",
                worker_id="w1",
                exit_code=0,
            )
        )
