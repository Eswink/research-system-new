"""M16 WP3 ExecutionJobQueue contract suite (Fake + PostgreSQL)."""

from __future__ import annotations

from collections.abc import Callable

import pytest

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
def test_record_result_settles_job(factory: Callable[[], object]) -> None:
    queue: ExecutionJobQueue = factory()  # type: ignore[assignment]
    task_id = queue.enqueue(_request("settle-1"))
    queue.record_result(
        ExecutionJobResult(
            task_id=task_id,
            lease_id="lease-1",
            fence=1,
            status="SUCCEEDED",
            exit_code=0,
            stdout_digest="sha256:out",
        )
    )
    outcome = queue.poll(task_id)
    assert outcome is not None
    assert outcome.status == "SUCCEEDED"
    assert outcome.exit_code == 0


@pytest.mark.parametrize("factory", _FACTORIES)
def test_cancel_flag_roundtrip(factory: Callable[[], object]) -> None:
    queue: ExecutionJobQueue = factory()  # type: ignore[assignment]
    task_id = queue.enqueue(_request("cancel-1"))
    assert queue.cancel_requested(task_id) is False
    queue.request_cancel(task_id)
    assert queue.cancel_requested(task_id) is True
