"""Cooperative cancellation signals for the worker loop (M17 WP4c + shutdown).

The execution backend calls the probe between wait steps. Two sources abort an
in-flight run:

- the Control Plane's cancel flag: an HTTP poll throttled to at most one request
  per interval, so a long container job does not hammer the gateway;
- a local shutdown request (SIGTERM), which is NEVER throttled — a shutdown must
  not wait behind a poll interval.

A poll failure never cancels the job (fail-safe: keep running; the lease renewal
path reports). Only a local shutdown sets `aborted_by_shutdown`, which the loop
reads to know that this worker no longer speaks for the attempt.
"""

from __future__ import annotations

import time
from collections.abc import Callable


class CancelProbe:
    """Throttled gateway cancel poll plus an unthrottled shutdown signal."""

    def __init__(
        self,
        *,
        task_id: str,
        cancel_requested: Callable[[str], bool],
        should_stop: Callable[[], bool],
        interval_seconds: float,
    ) -> None:
        self._task_id = task_id
        self._cancel_requested = cancel_requested
        self._should_stop = should_stop
        self._interval = max(0.5, interval_seconds)
        self._last = -self._interval
        self.aborted_by_shutdown = False

    def __call__(self) -> bool:
        if self._should_stop():
            self.aborted_by_shutdown = True
            return True
        now = time.monotonic()
        if now - self._last < self._interval:
            return False
        self._last = now
        try:
            return self._cancel_requested(self._task_id)
        except Exception:  # noqa: BLE001 - cancel probe must never kill a job
            return False


__all__ = ["CancelProbe"]
