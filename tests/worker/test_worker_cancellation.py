"""Cooperative cancel probe tests: throttled gateway poll + local shutdown.

M17 WP4c gave the probe one source (the Control Plane's cancel flag, polled on a
throttled cadence). Local shutdown added a second source that must NOT be
throttled — a SIGTERM cannot wait behind a poll interval.
"""

from __future__ import annotations

from collections.abc import Callable

from services.worker.cancellation import CancelProbe


def _recorder(calls: list[str], *, answer: bool) -> Callable[[str], bool]:
    def _record(task_id: str) -> bool:
        calls.append(task_id)
        return answer

    return _record


def test_shutdown_aborts_without_touching_the_gateway() -> None:
    calls: list[str] = []
    probe = CancelProbe(
        task_id="task-1",
        cancel_requested=_recorder(calls, answer=False),
        should_stop=lambda: True,
        interval_seconds=30.0,
    )

    assert probe() is True
    assert probe.aborted_by_shutdown is True
    assert calls == []  # shutdown short-circuits: no throttled poll needed


def test_gateway_poll_runs_immediately_then_throttles() -> None:
    calls: list[str] = []
    probe = CancelProbe(
        task_id="task-1",
        cancel_requested=_recorder(calls, answer=True),
        should_stop=lambda: False,
        interval_seconds=30.0,
    )

    assert probe() is True  # the first poll always goes out
    assert probe() is False  # suppressed inside the interval
    assert probe.aborted_by_shutdown is False
    assert calls == ["task-1"]


def test_poll_failure_never_cancels_the_job() -> None:
    def _boom(_task_id: str) -> bool:
        raise RuntimeError("gateway unreachable")

    probe = CancelProbe(
        task_id="task-1",
        cancel_requested=_boom,
        should_stop=lambda: False,
        interval_seconds=0.0,
    )

    assert probe() is False  # fail-safe: keep running, renewal path reports
    assert probe.aborted_by_shutdown is False
