"""Bounded decimal observations without changing the legacy wire field."""

from __future__ import annotations

from decimal import Decimal

from packages.domain.workspace import ExecutionRun


def seconds_observation(run: ExecutionRun, key: str = "gpu_elapsed_seconds") -> str | None:
    value = run.compute_usage_summary.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return None
    seconds = Decimal(str(value))
    if not seconds.is_finite() or not 0 <= seconds <= 31536000:
        return None
    return str(seconds.quantize(Decimal("0.000001")))
