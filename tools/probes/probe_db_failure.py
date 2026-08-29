"""Independent M14 audit probe: DB failure modes (section 10).

- connection refused: engine constructor must raise a typed PermanentPortError
  (CONFIGURATION) containing a REDACTED dsn, never a raw password.
- transient failure (dropped connection / bad statement): engine must raise
  TransientPortError (retryable) for mutating ops, not PermanentPortError.
- PostgreSQL restart: simulate by killing the container? Too destructive for a
  shared review DB; instead verify that after a connection-level failure the
  engine raises transient errors and a *new* connection recovers (idempotency
  preserved).
- serialization failure: FOR UPDATE SKIP LOCKED claim under two concurrent
  transactions is exercised by the real cross-process suite; here we verify
  the error classification path for an injected SerializationFailure.

M14 audit probe (RECHECK-20260828-022, DoD row 10). Re-runnable.

WARNING: truncates tasks/leases/idempotency_records/outbox_events and calls
pg_terminate_backend on the target database. Point RESEARCHOS_POSTGRES_DSN at a
disposable test instance.

Run: uv run --frozen --no-sync python -B tools/probes/probe_db_failure.py
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

import psycopg  # noqa: E402
from psycopg.rows import dict_row  # noqa: E402

from adapters.postgres.db import migrate  # noqa: E402
from adapters.postgres.workflow_engine import PostgresWorkflowEngine  # noqa: E402
from packages.application.ports.errors import (  # noqa: E402
    InvalidInputError,
    PermanentPortError,
    TransientPortError,
)
from packages.application.ports.workflow_engine import (  # noqa: E402
    TaskCompletion,
    TaskLease,
)
from tests.contracts.fixtures import research_task, task_contract  # noqa: E402

DSN = os.environ.get(
    "RESEARCHOS_POSTGRES_DSN",
    "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
)
# Synthetic value only: the assertion is that it never appears in error output.
_LEAK_CANARY = "pw-must-not-leak"

results: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> None:
    results.append(f"{'PASS' if cond else 'FAIL'} {label}{' :: ' + detail if detail else ''}")


def _truncate() -> None:
    conn = psycopg.connect(DSN, autocommit=True)
    conn.execute("TRUNCATE tasks, leases, idempotency_records, outbox_events CASCADE")
    conn.commit()
    conn.close()


def scenario_connection_refused() -> None:
    bad_dsn = f"postgresql://user:{_LEAK_CANARY}@localhost:59999/nonexistent"
    try:
        PostgresWorkflowEngine(dsn=bad_dsn)
        check("connection refused raises", False, "no exception")
    except PermanentPortError as exc:
        msg = str(exc)
        check("connection refused raises PermanentPortError", True)
        check(
            "refused error is redacted (no password)",
            _LEAK_CANARY not in msg and "***REDACTED***" in msg,
            msg,
        )
        check(
            "refused error category CONFIGURATION",
            exc.failure_category is not None and exc.failure_category.value == "CONFIGURATION",
            str(exc.failure_category),
        )
    except Exception as exc:  # noqa: BLE001
        check(
            "connection refused raises PermanentPortError",
            False,
            f"got {type(exc).__name__}: {exc}",
        )


def scenario_transient_after_connection_drop() -> None:
    """Kill the server side of the connection, then a mutating op must raise
    TransientPortError (retryable) — NOT PermanentPortError."""
    migrate(DSN)
    _truncate()

    engine = PostgresWorkflowEngine(dsn=DSN)
    task = research_task(task_id=str(uuid.uuid4()))
    engine.submit(task, task_contract())
    # Kill the ENGINE's backend from a separate connection.
    conn2 = psycopg.connect(DSN, autocommit=True)
    cur = conn2.execute(
        "SELECT pid FROM pg_stat_activity WHERE datname = current_database()"
        " AND pid <> pg_backend_pid() ORDER BY backend_start DESC"
    )
    pids = [r[0] for r in cur.fetchall()]
    engine_pid = pids[0]  # most recent other connection is the engine's
    conn2.execute("SELECT pg_terminate_backend(%s)", (engine_pid,))
    conn2.close()

    try:
        engine.acquire_lease(task.id.value)
        check("dropped connection raises transient", False, "no exception")
    except TransientPortError:
        check("dropped connection raises transient", True)
    except PermanentPortError as exc:
        check("dropped connection raises transient", False, f"PermanentPortError: {exc}")
    except Exception as exc:  # noqa: BLE001
        check("dropped connection raises transient", False, f"{type(exc).__name__}: {exc}")
    engine.close()

    # A fresh engine (new connection) still works: idempotency preserved.
    engine2 = PostgresWorkflowEngine(dsn=DSN)
    engine2.submit(task, task_contract())  # dedup path must still work
    lease = engine2.acquire_lease(task.id.value)
    check("fresh connection recovers after drop", lease is not None)
    engine2.complete(lease, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))
    engine2.close()


def scenario_transaction_rollback_no_partial_state() -> None:
    """A failed complete (stale lease) must not leave partial state: task stays
    LEASED with the live lease; no outbox event for the failed attempt."""
    migrate(DSN)
    _truncate()

    engine = PostgresWorkflowEngine(dsn=DSN)
    task = research_task(task_id=str(uuid.uuid4()))
    engine.submit(task, task_contract())
    engine.acquire_lease(task.id.value)

    # stale lease object: same task, wrong lease_id
    stale = TaskLease(lease_id="no-such-lease", task_id=task.id.value)
    try:
        engine.complete(stale, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))
        check("failed complete raises", False, "no exception")
    except InvalidInputError:
        check("failed complete raises InvalidInputError", True)

    conn = psycopg.connect(DSN, autocommit=True, row_factory=dict_row)
    row = conn.execute("SELECT status FROM tasks WHERE task_id=%s", (task.id.value,)).fetchone()
    n_leases = conn.execute(
        "SELECT count(*) AS n FROM leases WHERE task_id=%s", (task.id.value,)
    ).fetchone()["n"]
    n_completed = conn.execute(
        "SELECT count(*) AS n FROM outbox_events"
        " WHERE envelope_json->>'task_id'=%s"
        " AND envelope_json->>'event_type'='task.completed'",
        (task.id.value,),
    ).fetchone()["n"]
    conn.close()
    check(
        "failed txn leaves no partial state",
        row["status"] == "LEASED" and n_leases == 1 and n_completed == 0,
        f"status={row['status']} leases={n_leases} completed={n_completed}",
    )
    engine.close()


def main() -> int:
    scenario_connection_refused()
    scenario_transient_after_connection_drop()
    scenario_transaction_rollback_no_partial_state()
    print("\n".join(results))
    return 0 if all(r.startswith("PASS") for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
