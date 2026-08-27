"""Periodic self-healing for expired leases (M14 Production).

WP2 requirement: `recover_expired_leases` must run periodically, not only
lazily in `RunOrchestrationService.start_run`.

This module provides a lightweight background-thread scheduler that starts
in the composition root's lifespan. No APScheduler dependency — stdlib only.

Idempotent, `FOR UPDATE SKIP LOCKED` in engine, concurrent-safe.
"""

from __future__ import annotations

import threading
from typing import Any


class LeaseRecoveryScheduler:
    """Background daemon that calls `workflow.recover_expired_leases()` on interval.

    No new Port — it operates on the existing WorkflowEngine port.
    """

    def __init__(
        self,
        workflow: Any,
        *,
        interval_seconds: float = 30.0,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be > 0")
        self._workflow = workflow
        self._interval = interval_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="lease-recovery", daemon=True)
        self._thread.start()

    def stop(self, *, timeout: float = 2.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None

    def _run(self) -> None:
        # Jitter not needed for single-thread; keep simple
        while not self._stop.wait(self._interval):
            try:
                self._workflow.recover_expired_leases()
            except Exception:
                # Never crash scheduler on transient DB failure; engine maps to
                # TransientPortError or InvalidInputError — both non-fatal here.
                continue
