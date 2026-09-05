"""M14 PG crash/restart E2E (WP-H4).

Real subprocess A seeds + claims, then hard-kills itself (os._exit) — no
graceful shutdown. Process B (identical normal composition) recovers the
stale lease with real wall-clock TTL, reclaims, and completes. Canonical
state must live in PostgreSQL; no duplicate facts, no stuck RUNNING,
no orphan lease, no illegal transition.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from adapters.postgres.db import migrate

pytestmark = pytest.mark.postgres

_DB = "postgresql://research_os:research_os_m14_test@localhost:15432/research_os"
_ENV = os.environ.copy()
_ENV["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])
_ENV["RESEARCHOS_POSTGRES_DSN"] = os.environ.get("RESEARCHOS_POSTGRES_DSN", _DB)
_HELPER = str(Path(__file__).resolve().parents[1] / "postgres" / "worker_cross_process.py")


def _run(*args: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", _HELPER, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=_ENV,
    )


def _clean() -> None:
    import psycopg

    migrate(_ENV["RESEARCHOS_POSTGRES_DSN"])
    conn = psycopg.connect(_ENV["RESEARCHOS_POSTGRES_DSN"], autocommit=True)
    conn.execute("TRUNCATE tasks, leases, idempotency_records, outbox_events CASCADE")
    conn.commit()
    conn.close()


def _status(task_id: str) -> str:
    import psycopg
    from psycopg.rows import dict_row

    conn = psycopg.connect(_ENV["RESEARCHOS_POSTGRES_DSN"], autocommit=True, row_factory=dict_row)
    row = conn.execute("SELECT status FROM tasks WHERE task_id=%s", (task_id,)).fetchone()
    conn.close()
    return row["status"] if row else "MISSING"


def _count(column: str, task_id: str | None = None) -> int:
    import psycopg
    from psycopg.rows import dict_row

    conn = psycopg.connect(_ENV["RESEARCHOS_POSTGRES_DSN"], autocommit=True, row_factory=dict_row)
    if task_id is not None:
        cur = conn.execute(f"SELECT count(*) AS n FROM {column} WHERE task_id=%s", (task_id,))
    else:
        cur = conn.execute(
            "SELECT count(*) AS n FROM outbox_events "
            "WHERE envelope_json->>'event_type' = 'task.completed'"
        )
    row = cur.fetchone()
    conn.close()
    assert row is not None
    return int(row["n"])


def _script_a() -> str:
    return (
        "import os;"
        "from adapters.postgres.workflow_engine import PostgresWorkflowEngine;"
        "from tests.contracts.fixtures import research_task, task_contract;"
        "e=PostgresWorkflowEngine(dsn=os.environ['RESEARCHOS_POSTGRES_DSN'], lease_ttl_seconds=5);"
        "t=research_task(); e.submit(t, task_contract());"
        "lease=e.acquire_lease(t.id.value);"
        "print(f'TASK={t.id.value}', flush=True);"
        "print(f'LEASE={lease.lease_id}', flush=True);"
        "os._exit(9)"
    )


def test_pg_crash_restart_recovers_and_completes() -> None:
    """Process A hard-killed mid-run; Process B recovers and finishes the task."""
    _clean()
    pa = subprocess.run(
        [sys.executable, "-B", "-c", _script_a()],
        capture_output=True,
        text=True,
        timeout=60,
        env=_ENV,
    )
    task_line = [ln for ln in pa.stdout.splitlines() if ln.startswith("TASK=")]
    assert task_line, pa.stderr
    task_id = task_line[0].split("=")[1]
    assert pa.returncode == 9, "expected hard kill"
    assert _count("leases", task_id) == 1, "lease should exist after hard kill"

    time.sleep(9)  # lease expiry (real TTL 5s + slack)

    rec = _run("recover")
    assert "n=1" in rec.stdout, f"expected recovery of 1: {rec.stdout}"
    assert _status(task_id) == "QUEUED"
    assert _count("leases", task_id) == 0, "no orphan lease allowed"

    comp = _run("claim-complete", task_id, "60")
    assert comp.returncode == 0, comp.stderr
    assert _status(task_id) == "SUCCEEDED"
    assert _count("tasks", task_id) == 1, "single canonical task row"
    assert _count("completed") == 1, "single task.completed event"
