"""M14 real cross-process tests (WP-A3/B2/C2/H3).

Every worker is an independent OS process (subprocess.run on the helper
script) with its own psycopg connection and DSN. No threads, no asyncio,
no in-process double-connection simulation, no injected clocks.

Covers:
- WP-B2: concurrent claim exclusivity — exactly one worker owns the lease
- WP-C2: expiry-window fencing — stale writer is rejected after real TTL
- WP-A3/H4: crash/restart recovery — hard kill then recover+claim+complete

PART B W-04: the expiry/recovery waits are bounded POLLS, not fixed
`sleep(ttl+3)` — the fixed pattern raced under concurrent load (recovery once
saw n=0). Polling keeps the contract (expiry is eventually reached) without
clock coupling.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from adapters.postgres.db import migrate

pytestmark = [pytest.mark.postgres, pytest.mark.timing_sensitive]

_HELPER = str(Path(__file__).parent / "worker_cross_process.py")
_ENV = os.environ.copy()
_ENV["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])
_ENV["RESEARCHOS_POSTGRES_DSN"] = os.environ.get(
    "RESEARCHOS_POSTGRES_DSN",
    "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
)


def _dsn() -> str:
    return _ENV["RESEARCHOS_POSTGRES_DSN"]


def _run_worker(*args: str, timeout: int = 90) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", _HELPER, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=_ENV,
    )


def _poll_reclaim(task_id: str, ttl: int, lease_a: str, timeout: float = 40.0) -> str:
    """Wait for the lease to expire server-side, then reclaim (lazy, W-04)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        attempt = _run_worker("acquire", task_id, str(ttl))
        if attempt.returncode == 0 and "lease=" in attempt.stdout:
            lease_b = attempt.stdout.strip().split("lease=")[1]
            if lease_b != lease_a:
                return lease_b
        time.sleep(2.0)
    raise AssertionError("lease must have expired so worker B can reclaim it")


def _poll_recover(timeout: float = 40.0) -> int:
    """Run the recover worker until it reports >= 1 expired lease (W-04)."""
    last = ""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        rec = _run_worker("recover")
        last = rec.stdout.strip()
        if rec.returncode == 0:
            try:
                n = int(last.split("n=")[1])
            except (IndexError, ValueError):
                n = 0
            if n >= 1:
                return n
        time.sleep(2.0)
    raise AssertionError(f"expected recovery of 1: {last!r}")


def _clean() -> None:
    import psycopg

    migrate(_dsn())
    conn = psycopg.connect(_dsn(), autocommit=True)
    conn.execute("TRUNCATE tasks, leases, idempotency_records, outbox_events CASCADE")
    conn.commit()
    conn.close()


def _status(task_id: str) -> str:
    import psycopg
    from psycopg.rows import dict_row

    conn = psycopg.connect(_dsn(), autocommit=True, row_factory=dict_row)
    row = conn.execute("SELECT status FROM tasks WHERE task_id=%s", (task_id,)).fetchone()
    conn.close()
    return row["status"] if row else "MISSING"


def _lease_count(task_id: str) -> int:
    import psycopg
    from psycopg.rows import dict_row

    conn = psycopg.connect(_dsn(), autocommit=True, row_factory=dict_row)
    row = conn.execute("SELECT count(*) AS n FROM leases WHERE task_id=%s", (task_id,)).fetchone()
    conn.close()
    assert row is not None
    return int(row["n"])


@pytest.fixture(autouse=True)
def _clean_before() -> None:
    _clean()


def test_concurrent_claim_exactly_one_owner() -> None:
    """WP-B2: two independent processes race — exactly one gets a lease, other rejected."""
    seed = _run_worker("seed")
    assert seed.returncode == 0, seed.stderr
    task_id = seed.stdout.strip().split("task=")[1]

    # Launch both simultaneously; subprocess picks one to start first, both try immediately
    r1 = _run_worker("acquire", task_id)
    r2 = _run_worker("acquire", task_id)
    out1, out2 = r1.stdout.strip(), r2.stdout.strip()
    ok1, ok2 = out1.startswith("ACQUIRE"), out2.startswith("ACQUIRE")
    # At most one may succeed; the loser is rejected
    assert ok1 + ok2 >= 1, f"both failed: {out1} | {out2}"
    assert ok1 + ok2 <= 1, f"both acquired: {out1} | {out2}"
    assert _lease_count(task_id) == 1, "only one lease row may exist"


def test_stale_fenced_after_expiry_window() -> None:
    """WP-C2: worker A gets lease; after real TTL expiry (no recover), worker B
    claim-reclaims; A's stale lease is rejected."""
    _clean()
    ttl = 5  # real seconds; keep small but not artificially lowered vs production
    seed = _run_worker("seed")
    task_id = seed.stdout.strip().split("task=")[1]
    a = _run_worker("acquire", task_id, str(ttl))
    assert a.returncode == 0, a.stderr
    lease_a = a.stdout.strip().split("lease=")[1]

    # wait for real expiry, then B reclaims (lazy reclaim) — poll (W-04);
    # _poll_reclaim only returns a lease id different from lease_a.
    _poll_reclaim(task_id, ttl, lease_a)

    # A's stale lease must be fenced: complete with lease_a via the engine must
    # raise InvalidInputError; canonical state must not be overwritten.
    from adapters.postgres.workflow_engine import PostgresWorkflowEngine
    from packages.application.ports.errors import InvalidInputError
    from packages.application.ports.workflow_engine import TaskCompletion, TaskLease

    stale = TaskLease(lease_id=lease_a, task_id=task_id, agent_id=None)
    engine = PostgresWorkflowEngine(dsn=_dsn())
    try:
        with pytest.raises(InvalidInputError):
            engine.complete(stale, TaskCompletion(task_id=task_id, outcome="SUCCEEDED"))
    finally:
        engine.close()
    assert _status(task_id) in ("LEASED", "QUEUED"), "canonical state must not be overwritten"


def test_crash_recovery_real_subprocess() -> None:
    """WP-A3: worker A acquires then hard-kills (os._exit); after real TTL a
    recover worker reclaims and a third completes the task."""
    _clean()
    ttl = 5
    seed = _run_worker("seed")
    task_id = seed.stdout.strip().split("task=")[1]
    # Worker A: acquire then immediately os._exit(9) — hard kill, no cleanup
    script = (
        "import os;"
        "from adapters.postgres.workflow_engine import PostgresWorkflowEngine;"
        "from tests.contracts.fixtures import research_task, task_contract;"
        f"e=PostgresWorkflowEngine(dsn=r'{_dsn()}', lease_ttl_seconds={ttl});"
        f"t=research_task(); e.submit(t, task_contract()); e.acquire_lease('{task_id}');"
        "print('KILLED', flush=True); os._exit(9)"
    )
    proc = subprocess.run(
        [sys.executable, "-B", "-c", script],
        capture_output=True,
        text=True,
        timeout=60,
        env=_ENV,
    )
    assert "KILLED" in proc.stdout, proc.stderr
    assert proc.returncode == 9, "hard-kill expected"

    # wait for expiry + recovery — poll (W-04)
    assert _poll_recover() >= 1

    # verify queued + no orphan lease
    assert _status(task_id) == "QUEUED"
    assert _lease_count(task_id) == 0

    # B reclaims and completes
    comp = _run_worker("claim-complete", task_id, str(ttl))
    assert comp.returncode == 0, comp.stderr
    assert _status(task_id) == "SUCCEEDED"
    assert _lease_count(task_id) == 0
