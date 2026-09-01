"""Deterministic ExecutionBackend for the M16 distributed E2E gate (WP4).

Honest test double: it runs no container and no host shell — it produces a
deterministic, bounded ExecutionRun and writes real stdout.log/stderr.log into
the mounted workspace so the artifact/fencing/failover planes are exercised
end-to-end. The real Docker remote-execution E2E is covered by
`requires_docker`-marked tests (M16 plan §16).

M17 WP4c: the cooperative `cancelled` probe is honored — the delay loop
checks it in chunks and returns a CANCELLED run, so cancel propagation is
exercised by the offline distributed gate the same way the real container
path (DockerExecutionBackend._wait) honors it.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

from packages.domain.core import Digest, Timestamp
from packages.domain.workspace import ExecutionRun, ExecutionSpec, ExecutionStatus

_STDOUT_LOG = "stdout.log"
_STDERR_LOG = "stderr.log"
_CANCEL_CHECK_STEP = 0.25


class DeterministicExecutionBackend:
    """Bounded no-op execution: deterministic outputs, no side channels.

    `RESEARCHOS_WORKER_EXECUTE_DELAY_SECONDS` (read once per execute) lets the
    distributed E2E hold a claimed job in-flight long enough to observe lease
    expiry/failover — the only knob, and it delays nothing else.
    """

    def execute(
        self,
        spec: ExecutionSpec,
        timeout_seconds: int | None = None,
        *,
        cancelled: Callable[[], bool] | None = None,
    ) -> ExecutionRun:
        started = Timestamp.now()
        delay = float(os.environ.get("RESEARCHOS_WORKER_EXECUTE_DELAY_SECONDS", "0").strip() or 0)
        was_cancelled = False
        if delay > 0:
            waited = 0.0
            while waited < min(delay, 120):
                if cancelled is not None and cancelled():
                    was_cancelled = True
                    break
                step = min(_CANCEL_CHECK_STEP, min(delay, 120) - waited)
                time.sleep(step)
                waited += step
        workspace = Path(spec.workspace_path) if spec.workspace_path else Path(".")
        workspace.mkdir(parents=True, exist_ok=True)
        stdout = f"ok {spec.command}\n".encode("utf-8")
        stderr = b""
        (workspace / _STDOUT_LOG).write_bytes(stdout)
        (workspace / _STDERR_LOG).write_bytes(stderr)
        return ExecutionRun(
            run_id=f"dexec-{uuid4().hex}",
            spec=spec,
            status=ExecutionStatus.CANCELLED if was_cancelled else ExecutionStatus.SUCCEEDED,
            started_at=started,
            completed_at=Timestamp.now(),
            exit_code=None if was_cancelled else 0,
            stdout_digest=Digest.of_bytes(stdout),
            stderr_digest=Digest.of_bytes(stderr),
            compute_usage_summary={"backend": "deterministic", "elapsed_seconds": int(delay)},
        )

    def close(self) -> None:
        return None
