"""Protocol-1 exact seconds extension is bounded and preserves old reports."""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from packages.domain.core import Timestamp
from packages.domain.workspace import ExecutionRun, ExecutionSpec, ExecutionStatus
from services.api.worker_gateway.dto import ResultSubmissionDto
from services.worker.计量观测v1 import seconds_observation


def _dto(**extra: object) -> ResultSubmissionDto:
    return ResultSubmissionDto.model_validate({
        "worker_id": "test-worker",
        "registration_generation": 1,
        "lease_id": "lease",
        "fence": 1,
        "status": "SUCCEEDED",
        **extra,
    })


def test_fractional_seconds_survive_worker_and_gateway() -> None:
    run = ExecutionRun(
        run_id="test-execution",
        spec=ExecutionSpec(backend_kind="DOCKER", command="true"),
        status=ExecutionStatus.SUCCEEDED,
        completed_at=Timestamp.now(),
        exit_code=0,
        compute_usage_summary={"gpu_elapsed_seconds": 1.7},
    )
    exact = seconds_observation(run)
    assert exact == "1.700000"
    assert _dto(gpu_elapsed_seconds_exact=exact).gpu_elapsed_seconds_exact == Decimal("1.7")
    assert _dto(gpu_elapsed_seconds=2).gpu_elapsed_seconds == 2
    assert _dto(gpu_elapsed_seconds=2).gpu_elapsed_seconds_exact is None


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-0.1", "31536001", "0.1234567"])
def test_invalid_exact_seconds_fail_closed(value: str) -> None:
    with pytest.raises(ValidationError):
        _dto(gpu_elapsed_seconds_exact=value)
